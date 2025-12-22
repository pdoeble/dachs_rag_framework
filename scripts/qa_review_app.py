import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st


def load_paths_config() -> Tuple[Path, Dict[str, str]]:
    """
    Loads config/paths/paths.json which is the single source of truth for workspace_root and subpaths.

    Expected format:
      {
        "workspace_root": "/beegfs/scratch/workspace/<workspace>",
        "paths": {
          "qa_candidates": "qa_candidates/jsonl",
          "qa_final": "qa_final/jsonl",
          "semantic_json": "semantic/json",
          "normalized_json": "normalized/json"
        }
      }
    """
    cfg_path = Path(__file__).resolve().parents[1] / "config" / "paths" / "paths.json"
    if not cfg_path.exists():
        st.error(f"Missing paths config: {cfg_path}. Please create it (single source of truth).")
        st.stop()

    with cfg_path.open("r", encoding="utf-8") as f:
        cfg = json.load(f)

    if "workspace_root" not in cfg or "paths" not in cfg:
        st.error(f"Invalid paths config format in {cfg_path}. Needs keys: workspace_root, paths.")
        st.stop()

    workspace_root = Path(cfg["workspace_root"])
    rel_paths = cfg["paths"]

    required_keys = ["qa_candidates", "qa_final", "semantic_json", "normalized_json"]
    missing = [k for k in required_keys if k not in rel_paths]
    if missing:
        st.error(f"paths.json missing required path keys: {missing}")
        st.stop()

    return workspace_root, rel_paths


def safe_read_first_jsonl_line(fp: Path) -> Optional[Dict[str, Any]]:
    try:
        with fp.open("r", encoding="utf-8") as f:
            line = f.readline()
        if not line.strip():
            return None
        return json.loads(line)
    except Exception:
        return None


def list_jsonl_files(dir_path: Path) -> List[Path]:
    if not dir_path.exists():
        return []
    return sorted([p for p in dir_path.glob("*.jsonl") if p.is_file()])


def doc_id_for_qa_file(fp: Path) -> str:
    rec = safe_read_first_jsonl_line(fp)
    if rec and isinstance(rec, dict) and rec.get("anchor_doc_id"):
        return str(rec["anchor_doc_id"])
    return fp.stem


@st.cache_data(show_spinner=False)
def load_qa_items(qa_file: str) -> List[Dict[str, Any]]:
    fp = Path(qa_file)
    items: List[Dict[str, Any]] = []
    with fp.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return items


def chunk_doc_id_from_chunk_id(chunk_id: str) -> str:
    if "_c" in chunk_id:
        return chunk_id.rsplit("_c", 1)[0]
    return ""


@st.cache_data(show_spinner=False)
def load_chunk_index(_doc_id: str, jsonl_file: str) -> Dict[str, Dict[str, Any]]:
    fp = Path(jsonl_file)
    idx: Dict[str, Dict[str, Any]] = {}
    if not fp.exists():
        return idx

    with fp.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            cid = rec.get("chunk_id")
            if cid:
                idx[str(cid)] = rec
    return idx


def resolve_chunk_record(
    chunk_id: str,
    workspace_root: Path,
    rel_paths: Dict[str, str],
    prefer_semantic: bool,
) -> Optional[Dict[str, Any]]:
    doc_id = chunk_doc_id_from_chunk_id(chunk_id)
    if not doc_id:
        return None

    sem_fp = workspace_root / rel_paths["semantic_json"] / f"{doc_id}.jsonl"
    norm_fp = workspace_root / rel_paths["normalized_json"] / f"{doc_id}.jsonl"

    candidates = [sem_fp, norm_fp] if prefer_semantic else [norm_fp, sem_fp]

    for fp in candidates:
        idx = load_chunk_index(doc_id, str(fp))
        if chunk_id in idx:
            return idx[chunk_id]

    return None


def format_source_compact(rec: Dict[str, Any]) -> str:
    title = rec.get("title") or ""
    source_path = rec.get("source_path") or ""
    meta = rec.get("meta") or {}
    page_start = meta.get("page_start", None)
    page_end = meta.get("page_end", None)

    label = title.strip() if title else (Path(source_path).stem if source_path else "Unknown source")

    def to_int(x: Any) -> Optional[int]:
        try:
            return int(x)
        except Exception:
            return None

    ps = to_int(page_start)
    pe = to_int(page_end)

    if ps is not None and pe is not None:
        ps_ui = ps + 1
        pe_ui = pe + 1
        if ps_ui == pe_ui:
            return f"{label} — p. {ps_ui}"
        return f"{label} — p. {ps_ui}–{pe_ui}"

    return label


def render_chunk_block(
    chunk_id: str,
    workspace_root: Path,
    rel_paths: Dict[str, str],
    prefer_semantic: bool,
    badges: List[str],
    score: Optional[float] = None,
) -> None:
    rec = resolve_chunk_record(chunk_id, workspace_root, rel_paths, prefer_semantic)

    header_left = chunk_id
    header_right_parts: List[str] = []
    if badges:
        header_right_parts.append(" / ".join(badges))
    if score is not None:
        header_right_parts.append(f"score={score:.4f}")
    header_right = " | ".join(header_right_parts).strip()

    with st.expander(f"{header_left}" + (f"    ({header_right})" if header_right else ""), expanded=False):
        if rec is None:
            st.error("Chunk not found in semantic/normalized store (doc_id mapping failed or file missing).")
            return
        st.caption(format_source_compact(rec))
        st.write(rec.get("content") or "")


st.set_page_config(page_title="DACHS QA Review", layout="wide")
st.title("DACHS QA Review")
st.caption("Review Q/A items from jsonl. Top: question/answer + used chunks. Bottom: full context & neighbors.")

workspace_root, rel_paths = load_paths_config()

qa_candidates_dir = workspace_root / rel_paths["qa_candidates"]
qa_final_dir = workspace_root / rel_paths["qa_final"]

colA, colB, colC, colD, colE = st.columns([1.2, 2.0, 2.5, 1.0, 1.2])

with colA:
    dataset = st.selectbox("Dataset", ["qa_candidates", "qa_final"], index=0)

with colB:
    prefer_semantic = st.toggle("Prefer semantic chunks", value=True)

qa_dir = qa_candidates_dir if dataset == "qa_candidates" else qa_final_dir
qa_files = list_jsonl_files(qa_dir)

if not qa_files:
    st.error(f"No .jsonl files found in {qa_dir}")
    st.stop()

doc_map = {doc_id_for_qa_file(fp): fp for fp in qa_files}
doc_ids = sorted(doc_map.keys())

with colC:
    selected_doc_id = st.selectbox("Document (doc_id)", doc_ids, index=0)

selected_qa_file = doc_map[selected_doc_id]
qa_items = load_qa_items(str(selected_qa_file))

if not qa_items:
    st.error(f"No QA items loaded from {selected_qa_file}")
    st.stop()


def qa_label(item: Dict[str, Any], i: int) -> str:
    anchor = item.get("anchor_chunk_id", "")
    q = (item.get("question") or "").strip().replace("\n", " ")
    if len(q) > 90:
        q = q[:90] + "…"
    return f"{i:04d} | {anchor} | {q}"


labels = [qa_label(it, i) for i, it in enumerate(qa_items)]

with colD:
    random_pick = st.button("🎲 Random")

with colE:
    selected_idx = st.selectbox("Question", list(range(len(labels))), format_func=lambda i: labels[i], index=0)

if random_pick:
    selected_idx = random.randrange(0, len(qa_items))

item = qa_items[selected_idx]

q = item.get("question", "")
a = item.get("answer", "")
difficulty = item.get("difficulty", "")
lang = item.get("language", "")
domain = item.get("domain", [])
trust = item.get("trust_level", "")

meta_line: List[str] = []
if difficulty:
    meta_line.append(f"difficulty={difficulty}")
if lang:
    meta_line.append(f"lang={lang}")
if domain:
    meta_line.append(f"domain={domain}")
if trust:
    meta_line.append(f"trust={trust}")

st.subheader("Question")
st.write(q)

st.subheader("Answer")
st.write(a)

if meta_line:
    st.caption(" | ".join(meta_line))

st.divider()
st.subheader("Used chunks (evidence)")

source_chunks = item.get("source_chunks") or []
anchor_chunk_id = item.get("anchor_chunk_id") or ""

if not source_chunks:
    st.warning("source_chunks is empty.")

for cid in source_chunks:
    badges = ["USED"]
    if cid == anchor_chunk_id:
        badges.append("ANCHOR")
    render_chunk_block(
        chunk_id=cid,
        workspace_root=workspace_root,
        rel_paths=rel_paths,
        prefer_semantic=prefer_semantic,
        badges=badges,
    )

st.divider()
st.subheader("Context (details)")

prov = item.get("provenance") or {}
faiss = prov.get("faiss") or {}
faiss_ids = faiss.get("neighbor_chunk_ids") or []
faiss_scores = faiss.get("neighbor_scores") or []
local_ids = prov.get("local_neighbor_chunk_ids") or []
context_chunks = item.get("context_chunks") or []

tab1, tab2, tab3, tab4 = st.tabs(["Anchor chunk", "FAISS neighbors", "Local neighbors", "Full context"])

with tab1:
    if not anchor_chunk_id:
        st.warning("anchor_chunk_id missing.")
    else:
        render_chunk_block(
            chunk_id=anchor_chunk_id,
            workspace_root=workspace_root,
            rel_paths=rel_paths,
            prefer_semantic=prefer_semantic,
            badges=["ANCHOR"],
        )

with tab2:
    if not faiss_ids:
        st.info("No FAISS neighbors in provenance.")
    else:
        if isinstance(faiss_scores, list) and len(faiss_scores) == len(faiss_ids):
            pairs = list(zip(faiss_ids, faiss_scores))
            pairs.sort(key=lambda x: x[1], reverse=True)
        else:
            pairs = [(cid, None) for cid in faiss_ids]

        top_k = st.slider("Show top-k", min_value=1, max_value=min(50, len(pairs)), value=min(15, len(pairs)))
        for cid, sc in pairs[:top_k]:
            badges = ["FAISS"]
            if cid in source_chunks:
                badges.append("USED")
            if cid == anchor_chunk_id:
                badges.append("ANCHOR")
            render_chunk_block(
                chunk_id=cid,
                workspace_root=workspace_root,
                rel_paths=rel_paths,
                prefer_semantic=prefer_semantic,
                badges=badges,
                score=sc if isinstance(sc, (int, float)) else None,
            )

with tab3:
    if not local_ids:
        st.info("No local neighbors in provenance.")
    else:
        for cid in local_ids:
            badges = ["LOCAL"]
            if cid in source_chunks:
                badges.append("USED")
            if cid == anchor_chunk_id:
                badges.append("ANCHOR")
            render_chunk_block(
                chunk_id=cid,
                workspace_root=workspace_root,
                rel_paths=rel_paths,
                prefer_semantic=prefer_semantic,
                badges=badges,
            )

with tab4:
    if not context_chunks:
        st.info("context_chunks empty.")
    else:
        for cid in context_chunks:
            badges = ["CONTEXT"]
            if cid in source_chunks:
                badges.append("USED")
            if cid == anchor_chunk_id:
                badges.append("ANCHOR")
            if cid in faiss_ids:
                badges.append("FAISS")
            if cid in local_ids:
                badges.append("LOCAL")
            render_chunk_block(
                chunk_id=cid,
                workspace_root=workspace_root,
                rel_paths=rel_paths,
                prefer_semantic=prefer_semantic,
                badges=badges,
            )

st.divider()
st.caption(f"Loaded QA file: {selected_qa_file}")
