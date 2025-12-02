# E-learning module "Introduction to bwHPC"

Link: <https://training.bwhpc.de/ilias.php?baseClass=illmpresentationgui&cmd=layout&ref_id=275&obj_id=4917>

## 1 Before You Start

### Before You Start

Hello,

"Introduction to bwHPC" introduces you to the bwUniCluster 2.0 and the four bwForClusters as well as their usage, and smoothes the way to the bwHPC Wiki. It is composed for beginners at the bwUniCluster 2.0 as well as for more advanced users.
Beginners may enjoy the page First Steps For Beginners. Chapters, pages and sections beginning with an asterisk * contain additional information and can be skipped while reading for the first time.

This eLearning module is partly based on the course "HPC in Baden-Württemberg" held at the Karlsruhe Institute of Technology (KIT), enlarged by some screencasts. You can find a list of all screencasts on the page Screencasts and Uploaded Files.

We have structured the chapters and pages in such a way that you can easily jump to the pages of your interest. All pages are arranged in the same manner. First, you will find short paragraphs and figures explaining something. Then, at the bottom of the pages, we list internal and external links for further reading:

Internal links to pages of this eLearning module that contain related topics.

Links to the bwHPC Wiki.

Links to information about HoreKa at KIT.

HoreKa is not a bwHPC cluster, but as some of you may later work on it, we have added some information about it in order to alleviate the transition from a Tier-3 system to a Tier-2 system.

There are some safety instructions concerning passwords, ssh keys as well as file and directory permission in this eLearning module. You can find a list of them at the end of the module.

And, finally, a few words about the notation used throughout this eLearning course:
Code and commands are marked in this way.
$ is the prompt of the interactive shell. The full prompt may look like:
    user@machine:path$
Commands are entered in the interactive shell session and have the following general structure:
$ command -option value
Variables in these < > brackets have to be replaced by their actual values.

The content of this eLearning module is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Germany license.

Enjoy the course!
Your bwhpc team

Contributors and co-workers

This eLearning module was developed by Bärbel Große-Wöhrmann together with other members of the bwHPC project using the slides of the course HPC in Baden-Württemberg held by Robert Barthel and his colleagues at the KIT.

The screencasts were produced by my colleagues at the computing centers of the Universities of Mannheim, Heidelberg and Ulm.

## 2 bwHPC: HPC in Baden-Württemberg

### Concept

About bwHPC and bwHPC-S5

Scientific computing in research, teaching, and studies has become more and more important over the past years. In order to further support this activity and to create better conditions, the implementation concept "bwHPC" for High Performance Computing in Baden-Württemberg has been developed. This concept includes the promotion of High Performance Computing (HPC) on all levels and complements the national and European supply concepts in the area of High Performance Computing. bwHPC provides a state-wide HPC infrastructure, federated user support in seven competence centers and a training programme.

The current implementation concept for HPC, Data Intensive Computing (DIC) and Large Scale Scientific Data Management (LS²DM) in Baden-Württemberg is a union of bwHPC and bwDATA and aims at installing the BaWü data federation. The main task of the accompanying state-wide project bwHPC-S5 is to embed current and future data storage systems into the federated HPC infrastructure to unify computing and data services from the user's point of view. S5 stands for "Scientific Simulation and Storage Support Services".

The bwHPC-S5 project is funded by the Ministry of Science, Research and Arts (MWK) of the state of Baden-Württemberg. The Universities of Freiburg, Heidelberg, Hohenheim, Konstanz, Mannheim, Stuttgart, Tübingen and Ulm, the Karlsruhe Institute of Technology, as well as the University of Applied Sciences in Esslingen participate in the realization of the project.

Figure 1: Brief answer.
Tier levels in Baden-Württemberg
HPC clusters are classified by their Tier level. The bwHPC clusters, the bwUniCluster 2.0 and the four bwForClusters, form the Tier-3 level in Baden-Württemberg (see Figure 2 below). The state research HPC cluster HoreKa (formerly ForHLR) at the Karlsruhe Institute of Technology (KIT) is a Tier-2 system, whereas the HPE Apollo (Hawk) at the High Performance Computing Center Stuttgart (HLRS) is both a national (Tier-1) and an European (Tier-0) HPC system.

Figure 2: The HPC systems in Baden-Württemberg. The supercomputer Hawk is a Tier-1 and Tier-0 system (national and European HPC center), HoreKa is a Tier-2 system (supraregional HPC center), and the bwForClusters as well as bwUniCluster 2.0 are Tier-3 systems.

### Infrastructure

As of 2018.
Figure 3 below shows the locations of the bwHPC clusters. Each cluster is dedicated to a special purpose and has the appropriate software and hardware configuration.

Figure 3: The bwHPC clusters at the Tier-3 level.

The table below lists the main features of the bwHPC clusters. More information about architecture and hardware configurations is presented in the chapter about hardware and architecture and in the bwHPC Wiki.

|                      | bwUniCluster2.0                                                                                                                                                                                                                                                                               | 4 bwForCluster                                                                                                                                                                                                                     |
|----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Location**         | • Karlsruhe                                                                                                                                                                                                                                                                                   | • Mannheim and Heidelberg<br>• Tübingen<br>• Ulm<br>• Freiburg                                                                                                                                                                      |
| **Shareholders**     | • The universities of: Freiburg, Tübingen, Heidelberg, Ulm, Hohenheim, Konstanz, Mannheim, Stuttgart, the KIT, and HAW BW e.V. (an association of universities of applied sciences in Baden-Württemberg)<br>• Baden-Württemberg’s ministry of science, research and arts (MWK)                 | • German Research Society (DFG)<br>• Baden-Württemberg’s ministry of science, research and arts (MWK)                                                                                                                              |
| **Access**           | • For all members of shareholder’s university in BW<br>• For all members of the universities of applied sciences in BW<br>• How? See the page about *Registration – bwUniCluster*                                                                                                            | • All university members in Baden-Württemberg<br>• How? See the chapter about *Registration – bwForCluster*                                                                                                                         |
| **Usage**            | • Free of charge<br>• For general purpose, teaching & education<br>• For technical computing (sequential & weak parallel) & parallel computing                                                                                                                                                 | • Free of charge<br>• Approved Compute Project Proposal to only one bwForCluster matching cluster’s subject fields                                                                                                                 |

### State-wide User Support

bwHPC-S5 provides support services for scientific simulation and data storage. Its goals are:
bridging science & HPC
bridging the HPC Tier levels and Large Scale Scientifc Data Facilities (LS2DM)
embedding services

Figure 4: The goals of bwHPC-S5.
The offers of bwHPC-S5 are:
bwHPC training sessions: Ten universities in Baden-Württemberg offer seminars and workshops about HPC.
Documentation and best practices repositories in the bwHPC Wiki
Software installed on the bwHPC clusters, see
<https://www.bwhpc.de/software.html>
Cluster Information System CIS
Providing and maintaining
community specific and HPC generic software and tools
data management tools for using e.g. bwDataArchive or SDS@hd
HPC and data competence centers
There are seven competence centers including a cross-sectoral team organized by eight universities. They provide science specific HPC support in the areas show in Figure 5:

Figure 5: The seven bwHPC-S5 competence centers.
The competence centers
establish state-wide experts pools,
coordinate Tiger Teams. Tiger teams provide extensive user support and assist with
code adaptation,
workflow adaptation,
porting,
parallelisation,
identify user key topics,
help to access the Tier-2 (HoreKa) and Tier-1 (Hawk) systems,
offer science specific HPC Best Practice Guides,
can be contacted by
email,
the trouble ticket system (bwSupportPortal) and
via the Call for Tiger Team support.
The members of the competence centers are experts from ten universities (see Figure 6):

Figure 6: The bwHPC-S5 experts come from ten universities in Baden-Württemberg.
Do you want to make a complaint? Or do you have a question concerning the bwHPC policy?
Send an email to: <office@bwHPC.de>
Open a trouble ticket and assign it to "bwHPC project management"
Contact your university member of the LNA-BW (User Steering Committee)

### * Governance

The bwHPC governance.
The User Steering Committee (Landesnutzerausschuss, LNA)
sets bwHPC access formalities,
assesses the bwHPC workload,
regulates the bwHPC cluster expansion,
assigns science communities to science clusters,
represents HPC users interests concerning:
resource demands,
HPC technologies,
software licences,
adjustment of resource quota

## 3 First Steps For Beginners

### First Steps For Beginners

This is a brief introduction for newcomers. Below, "cluster" means "bwUniCluster 2.0" or "bwForCluster".

Register yourself as described here.

Register a 2FA token.

Register a password.

Log in on the cluster: Linux users and Windows users.

The operating system of all clusters is Linux.  You can find basic Linux commands and some useful links here.

Transfer your data (source code, scripts, configuration files, ...) to the cluster: Linux users and Windows users.

A HPC cluster consists of login nodes, hundreds of multicore processors (called compute nodes) and storage systems connected by a high speed data network. Here, I give a short introduction to the hardware and architecture of a cluster and explain "cores", "shared memory" and things like that.

After logging in, you are in your home directory. In addition, there are working directories (workspaces) and temporary directories. Please find a brief overview here.

You can use the application software packages already installed on the clusters. To this end, you have to load the appropriate module files in your batch job scripts as described here.

You can run serial programs on single cores (serial jobs), or you can run parallelized programs on many cores of one or more compute nodes. In both cases (serial and parallel) you have to launch your program via the batch system as described here. You have to specify the requested resources (number and type of cores, amount of memory and walltime) in the batch job.

If you want to test your batch job script or your software, or if you are not sure how many memory your software needs, you can use interactive jobs for testing.

You can easily check and change the status of your batch jobs as described here.

## 4 Registration

### 4.1 bwUniCluster 2.0

The bwUniCluster 2.0 is a Tier-3 cluster for general purposes. Access is granted only for members of the shareholder universities. The users authenticate themselves with their usual university account via bwIDM, and the authorization is based on the bwUniCluster entitlement issued by the universities.

The registration procedure is built up of three steps:

Step A: Obtainment of bwUniCluster entitlement
Contact your university in order to get the bwUniCluster entitlement. Each university has its own entitlement granting policies!

Step A: Obtain the bwUniCluster entitlement from your university.
Step B: Web registration, 2-factor authentication and password
After getting the entitlement, you have to register yourself at the registration website <https://bwidm.scc.kit.edu/> of the provider. During the registration process you will register a 2FA token and set a password.

Step B: Registration at <https://bwidm.scc.kit.edu/>
Step C: bwUniCluster questionnaire
During or after the web registration you must fill out a short questionnaire. You will be asked about your scientific field, the numerical methods you use, your field of activity and your type of activity.
Please, fill out the questionnaire within 14 days after your registration. Otherwise, your bwUniCluster 2.0 account will be locked!

In the following screencast, Jürgen Salk (University of Ulm) explains the web registration (Step B).

Video Player

00:00
02:56

"Web registration for the bwUniCluster" (Jürgen Salk, University of Ulm). Lecture recording from an introductory course to bwHPC and the bwUniCluster held on 29th of June, 2015 at the University of Ulm.

### 4.2 bwForCluster

#### bwForCluster: Overview

The bwForClusters (JUSTUS 2, MLS&WISO, NEMO, BinAC) are Baden-Württemberg research clusters, they are Tier-3 systems. The architecture is optimized for certain scientific communities.

Access is granted for members of Baden-Württemberg's universities. The access process ensures using the suitable cluster and enhances user support. It consists of three steps:

Das Bild zeigt einen Nutzer, der drei Schritte durchläuft:

1. Der Nutzer sendet einen Antrag an die ZAS.  
2. Der Nutzer erhält eine Bestätigung bzw. Autorisierung von seiner Universität.  
3. Der Nutzer nutzt anschließend einen der bwForCluster (dargestellt durch mehrere farbige Cluster mit Servern und Symbolen).

Links befindet sich die ZAS, rechts die Universität. Unten sind mehrere bwForCluster als Servergruppen in verschiedenen Farben dargestellt.

bwForCluster: Registration progress. Blue paper: approval of CAT, green paper: obtainment of bwForCluster entitlement.
Step 1: Registration at the Central Application Site (ZAS) in order to get the approval of the Cluster Assignment Team (CAT).
Step 2: Obtainment of the bwForCluster entitlement from your university.
Step 3: Web registration at the bwForCluster site.

#### What is ZAS?

The Central Application Site (ZAS).
The ZAS (Central Application Site) is a web interface of the bwHPC clusters to handle the user compute activities.

At the ZAS, you register your planned compute activities (RV, Rechenvorhaben).

Each RV has a responsible person (RV responsible) who applies for the compute activity (RV registration). A RV may have additional team members (managers and coworkers, RV collaboration).

The Cluster Assignment Team (CAT) assigns the exact cluster according to the RV requirement.

The RV responsible person
is authorized to change roles (manager, coworker) of team members,
may de-/reactivate team members,
can renew passwords,
may apply for further resources (if approved),
has access to bwForCluster (if approval is valid).
The team members (managers, coworkers) have general rights and access to bwForCluster if the approval is valid.
There are additional manager rights: Managers are allowed to
read team details,
de-/reactivate coworkers.
A RV approval is valid for
one certain bwForCluster,
all team members,
a period of one year after the approval.
The starting point for the registration of a RV at the ZAS is <https://zas.bwhpc.de/en/zas_info_bwforcluster.php>.

At "RV registration", the applicant (RV responsible) describes the research objective, the used methods and the required software packages. Additionally, the resource requirements have to be specified: CPU hours, memory, disk space, ...

After approval of the RV by the CAT, coworkers and managers register themselves under "RV Collaboration".

#### Step 1: Registration at ZAS

First, the applicant registers the RV at the ZAS as describes above:

Then, the RV responsible gets his acronym and a password, and the Cluster Assignment Team (CAT) discusses the RV:

The RV responsible passes the acronym and the password down to the other team members, and the CAT approves or rejects the RV:

Finally, the RV responsible gets the approval of the CAT, and the team members register themselves at the ZAS as described above using the acronym and the password:

#### Step 2: Obtainment of the bwForCluster Entitlement

Obtaining the bwForCluster entitlement from your university is similar to getting the bwUniCluster entitlement as described on the page bwUniCluster 2.0. Each university has its own procedure. In the bwHPC Wiki you find more information.

#### Step 3: Web Registration at the bwForCluster Site

When the members of the RV team register themselves at the web registration of their bwForCluster, the registration server checks whether the home universities have issued the bwForCluster entitlements and whether the RV is approved:

### 4.3 HoreKa

#### HoreKa

HoreKa is formed from "Hochleistungsrechner Karlsruhe", a Tier 2 High Performance Computing system  at KIT.

Employees of all Universities and research institutes in Germany can request access to HoreKa by submitting a project proposal. Project managers of a foreign research organization need a german partner to submit the proposal.

## 5 2-Factor Authentication

### 2-Factor Authentication (2FA)

Besides your password you need a second factor, the Time-dependent One-Time Password (TOTP), in order to log into bwUniCluster 2.0.

TOTPs can be generated by

- an app on your smartphone or tablet
- a hardware token (e.g. Yubikey)
- an app running on an additional PC / notebook
It is very important that the device that generates the One-Time Passwords and the device which is used to log into bwUniCluster 2.0 are two different devices!

#### 2FA with smartphone

First of all, you have to install an app like FreeOTP or Google Authenticator on your smartphone or tablet. See bwHPC Wiki for a complete list of suitable apps and the required operating systems.

TOTP generated by FreeOTP on a smartphone
Next, you log in at <https://bwidm.scc.kit.edu/> and open "Meine Tokens" ("My Tokens"):

"Meine Tokens" at <https://bwidm.scc.kit.edu/>
You will see:

Click on "NEUES SMARTPHONE TOKEN". A new window opens:

Click on "Start". A QR code is generated which you scan with your smartphone app. The app generates a TOTP (six-digit code). Enter the code into the green box "Aktueller code" ("Current code") and click on "PRÜFEN" ("CHECK"):

If everything works fine, the new token (the app on your smartphone) is registered and you see

It is recommended to register more than one token, e.g. on another smartphone.

Finally, you should register a back-up TAN list by opening "NEUE TAN LISTE ANLEGEN" or "CREATE NEW TAN LIST":

Print the TAN list and keep it in a safe place. You will need it if you lose your smartphone or deinstall your app.

Your registered tokens and TAN list are presented similar to:

If you want to register new tokens later on, you have to enter a TOTP or the first TAN of your back-up TAN list ("Aktueller code", "Current code"):

##### 2FA with hardware token

Log in at <https://bwidm.scc.kit.edu/> and open "Meine Tokens" ("My Tokens"):

"Meine Tokens" at <https://bwidm.scc.kit.edu/>
If you have a hardware token (e.g. Yubikey), click on "NEUES YUBIKEY TOKEN" ("NEW YUBIKEY TOKEN"):

Enter the Yubikey into your computer and press the button on the Yubikey. Paste the code produced by your Yubikey into the green box "Aktueller code" ("Current code") and press "START":  

The remaining procedure is the same as that with "2FA with smartphone".

Note: It is highly recommended to create a back-up TAN list (see "2FA with smartphone").

#### 2FA with notebook

If you have neither a smartphone nor a hardware token, you can use an app like Authy (see the list of apps in the bwHPC Wiki for more details) running on another computer to generate TOTPs.

As Authy cannot scan QR codes, you have to install a QR code reader like the "CodeTwo QR Code Desktop Reader & Generator" for Windows 10 besides Authy (note the Heise tipp at <https://www.heise.de/tipps-tricks/QR-Code-scannen-am-PC-so-geht-s-5076050.html>).

The procedure to register a software token is the same as described in "2FA with smartphone" above besides that you have to scan the QR code with the QR code reader and paste the QR code reader's output following "secret=" into the Authy input field "Enter Code given by the website".

### FAQs about 2FA

#### Why do I need a backup TAN list?

Suppose, you have registered a token generated by a smartphone app as described on the page 2-Factor Authentication and this smartphone is broken.

If you login at <https://bwidm.scc.kit.edu/> in order to generate a new token, you see a screen similar to the following one:

German version.

English version.
Without a token of your backup TAN list or another, working token, you cannot login and generate a new token.

### 2FA and SSH Keys

#### Safety instructions

SSH keys should not be reused (i.e. do not copy the private key from one system to another).

SSH keys should be password protected if possible (unless they are used in automated workflows).

The directory .ssh must be readable and writable only for the owner, as well as private keys and the authorized_keys file.

SSH keys should be complex, i.e. comply with current standards (RSA with at least 2k or based on elliptic curves, no more DSA keys). Recommended ssh keys are:
2048 bits or more for RSA
521 bits for ECDSA
256 Bits (Default) for ED25519
ECDSA-SK and ED25519-SK keys (for use with U2F Hardware Tokens) cannot be used yet. (Source: bwHPC Wiki)
For some workflows it might be advantageous to use an interactive ssh key or a command ssh key.

You can use an interactive ssh key to log into bwUniCluster 2.0. After generating, adding and registering the key as described below, you have to log in with an One-Time Password (TOTP) and your password, and your ssh key is unlocked for one hour. If you want to login again during this hour, you don't have to enter a TOTP and your password because your ssh key is unlocked.
After the hour has passed, your ssh key is locked. If you want to login again now, you have to enter the OTP and your password, and then your ssh key will be unlocked for another hour.

Command ssh keys are restricted to single commands and a small number of IP addresses. They have to be checked and approved by an HPC administrator before they can be used. Their validity is reduced to one month.

Before logging into bwUniCluster 2.0 with an interactive ssh key, you have to register a token as described on the page 2-Factor Authentication.

#### Generating an Ed25519 ssh key with PuTTYgen

After starting PuTTYgen, choose "Ed25519" and click on "Generate":

Set a strong password (passphrase) and save the public and the private key somewhere on your notebook or PC.

#### Adding a ssh Key

Login at <https://bwidm.scc.kit.edu/> and open "Meine SSH Pubkeys" or "My SSH Pubkeys":

You will see:

German version.

Das Bild zeigt ein Formular zum Hinzufügen eines SSH Public Keys.

Oben steht „Add SSH Key“. Darunter Hinweise:

- Niemals den privaten Schlüssel weitergeben
- Privaten Schlüssel mit einem sicheren Passwort schützen

Es wird erklärt, dass das Format dem einer einzelnen Zeile aus `.ssh/authorized_keys` entspricht.

Im Formular gibt es zwei Felder:

- **SSH Key Name:** Eingabefeld mit dem Text „my_key“.
- **SSH Key:** Mehrzeiliges Feld mit dem sichtbaren Beginn eines öffentlichen SSH-Schlüssels, beginnend mit `Comment: "ed25519-key-20210812"` und dem Schlüsselstring.

Unten befindet sich ein Button mit der Beschriftung **ADD**.

English version.
Choose "SSH KEY HOCHLADEN" or "ADD SSH KEY". Then you will see:

German version.

English version.
Invent and enter a name ("SSH Key Name") and copy your public key into the box "SSH Key". Afterwards, click on "Hinzufügen" or "ADD". You will see a confirmation with the expiration date of the key:

German version.
Das Bild zeigt eine Übersicht der hinterlegten SSH-Schlüssel.

Überschrift: **List of ssh keys**

Ein Eintrag mit Namen **my_key** ist sichtbar.

Details zum Schlüssel:

- **Expires:** 10.11.2021 15:27  
- **Key type:** ssh-ed25519  
- **Fingerprint (SHA256):** IExb6PW7PW1aZUeS1/msRBHvdjdVSPA0edq6CmSKwig=

Unter „Services:“ steht nichts eingetragen.

Unten befindet sich ein Button **REVOKE** und darunter ein weiterer Button **ADD SSH KEY**.  
Link **Back** am unteren Rand.

English version.
The next step is to register your key as interactive key or as command key.

#### Registering an Interactive Key

Please follow the instructions in the bwHPC Wiki:
Interactive Keys are used for manual SSH logins to work on the cluster.

Key Validity and 2-Factor Authentication
Attention.svg
Regular SSH Keys require 2-factor unlock:

Keys are only valid for limited hours after entering OTP and service password
Must re-authenticate after validity expires
FIDO2 SSH Keys (ECDSA-SK/ED25519-SK) work differently:

Always valid - no 2-factor unlock needed
Authentication via physical key touch only
Recommended for best security and convenience
Available on: bwUniCluster 3.0 and NEMO 2 only (not on Helix)
Validity periods for regular SSH keys
Cluster Validity after 2FA Login
bwUniCluster 3.0 8 hours
bwForCluster Helix 12 hours
bwForCluster NEMO 2 12 hours
Registration Steps

1. Add your SSH key if not already done

2. Navigate to Registered Services / Registrierte Dienste → Click Set SSH Key / SSH Key setzen for your cluster

Select cluster
3. Find your key in the bottom section → Click Add / Hinzufügen

Add SSH key to service
4. Select Interactive as usage type → Add optional comment → Click Add / Hinzufügen

Set as Interactive key
5. Done! Your key is now active for interactive logins

SSH key registered

#### Registering a Command Key

Command Keys enable automated workflows without manual login (e.g., automated backups, data transfers).

Security Requirements
Attention.svg
Command keys are always valid (no 2FA required), making them high-value targets.

Mandatory restrictions:

Single command: Must specify exact command with full path
IP restriction: Limited to specific IP address(es) or subnet
Admin approval: Keys must be reviewed before activation
Short validity: Maximum 30 days
Common use case: For rsync data transfers, see the rrsync wiki guide.

Registration Steps

1. Add your SSH key if not already done

2. Navigate to Registered Services → Click Set SSH Key for your cluster

Select cluster
3. Find your key in the bottom section → Click Add / Hinzufügen

Add SSH key to service
4. Configure command restrictions:

Usage type: Select Command
Command: Enter full path and parameters (example for rrsync below)
From: Specify IP address, range, or subnet (see man 8 sshd)
Comment: Explain purpose (speeds up approval)
Click Add / Hinzufügen
Example: rrsync for automated data transfer
/usr/local/bin/rrsync -ro /home/aa/aa_bb/aa_abc1/
Note: Verify the exact path on your cluster first (may be /usr/bin/rrsync)

Configure command key
5. Wait for approval: Key status shows Pending until an administrator approves it

Key pending approval
You'll receive an email when the key is approved and ready to use.

#### Revoking SSH Keys

Revoked keys are immediately disabled and cannot be reused.

1. Navigate to your cluster's SSH key management:

bwUniCluster 3.0
bwForCluster Helix
bwForCluster NEMO 2

My SSH Pubkeys page
2. Click REVOKE / ZURÜCKZIEHEN next to the key you want to disable

Revoke SSH key

## 6 Service Password for bwUniCluster 2.0

### bwUniCluster 2.0 Password

bwUniCluster 2.0 Password
Safety instructions

The same credentials (passwords) must not be used for different accesses (accounts).

Passwords should be at least 8 characters long.

Passwords should be complex, i.e., they should not consist of words found in (electronic) dictionaries, and they should contain different classes of characters (lowercase and uppercase letters, numbers, and special characters), be as well mixed as possible, and not be arranged in a simple pattern on the keyboard.

Passwords should still be easy to remember (e.g., with the help of a mnemonic whose first letters, punctuation marks, and numbers form the password).

Passwords should not be written down, at least not stored in plain text or on a piece of paper that is easily accessible.

Passwords must be changed after every suspected hacker attack or virus infection.

During the registration process at <https://bwidm.scc.kit.edu/> you set your password for bwUniCluster 2.0.

After logging in via bwIDM, choose "Dienstpasswort setzen" ("Set service password") at

or

Then you can enter a new password:

It is highly recommended to use strong passwords and to change them regularly. Do not use the same password for two different accounts or services!

## 7 Login

Login: Linux User
In order to connect to and login on a cluster, you have to start a Secure Shell (ssh) with your user name and the hostname.

Your user name [< prefix >*]< username > may have a prefix indicating your home university, e. g. st* for Uni Stuttgart and ho_for Uni Hohenheim. Examples:
KIT user: ab1234
Student at Uni Hohenheim: ho_amuster
The hostnames of the bwHPC clusters are (selection):
bwUniCluster 2.0:
bwunicluster.scc.kit.edu or
uc2.scc.kit.edu
bwForCluster JUSTUS: justus2.uni-ulm.de
HoreKa: horeka.scc.kit.edu
 If you are in home office instead of in your campus office, you have to establish a VPN connection to your home institution (university) before you can log into bwUniCluster 2.0.

If you use Linux or Mac OS, you simply open a terminal and type the command
$ ssh -X [< prefix >_]< username >@< hostname >

Example:
$ ssh -X <ab1234@uc2.scc.kit.edu>

Then, you are asked to enter your TOTP
YOUR OTP:

and your password:
Password:

Then, you see the Message of the Day. Some basic Linux commands are presented in the Linux chapter. With exit you logout of bwUniCluster 2.0.

Das Bild zeigt ein Terminalfenster einer Ubuntu-VM (baerbel@baerbel-VirtualBox).

Ablauf:

- Zuerst wird der Cisco AnyConnect VPN-Client im Hintergrund gestartet:  
  `/opt/cisco/anyconnect/bin/vpnui &`

- Danach ein SSH-Login:  
  `ssh -X st_ac117776@uc2.scc.kit.edu`

- Eine Warnung erscheint, dass der ECDSA-Hostkey zur Liste der bekannten Hosts hinzugefügt wurde.

- Die Einmal-PIN (OTP) wird abgefragt und eingegeben:  
  `Your OTP: 300231`  
  Danach Eingabe des Passworts.

- Nach erfolgreichem Login erscheint die ASCII-Art-Begrüßung des **bwUniCluster2** inklusive Infos:
  - KITE 2.0, RHEL 8.2, Lustre 2.12.6
  - Links zu Wiki, Ticketsystem, Training
  - Kontaktadressen
  - Hinweis zu ablaufender Mathematica-Lizenz für Mannheim-Nutzer
  - Standort-News

- Abschließend Eingabe `exit`, der Nutzer wird abgemeldet.  
  Hinweis: „Connection to uc2.scc.kit.edu closed.“

Das Terminal kehrt zu:  
`baerbel@baerbel-VirtualBox:~$` zurück.

In the following screencast, Christian Greiner explains the login process.

Video Player

00:00
01:52
SSH – Script zum Videotutorial
Christian Greiner (Universitätsrechenzentrum Heidelberg)

1. Anmeldung mit SSH
Guten Tag,
in diesem Video möchte ich ihnen zeigen, wie sie sich über den SSH-Befehl auf den
bwUniCluster per Remote-Verbindung anmelden.
SSH steht für „Secure Shell“ und ermöglicht die Herstellung einer
verschlüsselten Netzwerkverbindung mit einem entfernten Gerät. (in diesem
Fall ein Computer)(Pause)
Beginnen wir zunächst mit der Anmeldung auf einen Linux-Rechner:
Dafür öffnen sie die Kommandozeile und geben den Befehl „ssh“ ein.
Danach geben sie ihren Benutzernamen an. Dieser setzt sich zusammen aus dem Kürzel ihrer
Heimat-Uni und dem dortigen Nutzernamen. Wenn sie beispielsweise angehöriger der Universität
Heidelberg sind, muss vor ihrer allgemeinen Nutzerkennung „hd_“ stehen. Nach der Angabe des
Benutzernamens folgt ein @-Zeichen und die Adresse des bwUniClusters. (bwunicluster.scc.kit.edu)
Drücken sie „Enter“.
Wenn man sich erstmals mit einem bisher unbekannten Server verbindet, zeigt die Kommandozeile
den Fingerabdruck des Serverzertifikates an. Hiermit kann man sicherstellen, dass man nicht mit
dem falschen Server verbunden ist, wie es z.B. bei einem „Man-In-The-Middle Angriff“ passieren
könnte.
Beim ersten Anmelden bestätigt man diese Information mit der Eingabe „yes“. Sollte das
Serverzertifikat und damit sein Fingerabdruck sich jemals ändern, wir eine Meldung in der
Kommandozeile sie hierauf hinweisen.
Wenn sie nun dies mit „yes“ akzeptiert haben, verlangt die Kommandozeile das Dienstpasswort,
welches sie bei der Registrierung für den Zugang zum bwUniCluster gesetzt haben.
Wenn sie nun dies mit „yes“ akzeptiert haben, verlangt die Kommandozeile das Dienstpasswort,
welches sie bei der Registrierung für den Zugang zum bwUniCluster gesetzt haben.
(Pause)
Nun sind sie erfolgreich auf dem bwUniCluster angemeldet.
(Pause)
Zum Abmelden vom bwUniCluster tippen sie den Befehl „exit“ ein.

"Login zum bwUniCluster" (ssh) by Christian Greiner (Universität Heidelberg).

### Login: Windows User

In order to connect to and login on a bwHPC cluster, you need your user name (often denoted by <UserID>) and the hostname of the cluster.

Your user name [< prefix >*]< username > may have a prefix indicating your home university, e. g. st* for Uni Stuttgart and ho_for Uni Hohenheim. Examples:
KIT user: ab1234
Student at Uni Hohenheim: ho_amuster
The hostnames of the bwHPC clusters are (selection):
bwUniCluster 2.0:
bwunicluster.scc.kit.edu
uc2.scc.kit.edu
bwForCluster JUSTUS: justus2.uni-ulm.de
HoreKa: horeka.scc.kit.edu
If you use Windows, you should connect to the cluster via MobaXterm.

 If you are in home office instead of in your campus office, you have to establish a VPN connection to your home institution (university) before you can log into bwUniCluster 2.0.

After installing and starting MobaXterm, click on "Session":

Choose the session type "SSH":

Enter the hostname ("Remote host") and your user name. Open "Advanced SSH settings" and check the box "X11-Forwarding" if you have graphic output. Choose SSH-brower type "SCP" for data transfer and click on "OK":

Das Bild zeigt die Session-Einstellungen eines SSH-Clients.

**Basic SSH settings**

- Remote host: `uc2.scc.kit.edu`
- Specify username: aktiviert, Benutzername: `st_ac123456`
- Port: 22

**Advanced SSH settings**

- X11-Forwarding: aktiviert
- Compression: aktiviert
- Remote environment: „Interactive shell“
- SSH-browser type: „SCP (normal speed)“
- Use private key: deaktiviert

Unten befinden sich die Buttons **OK** und **Cancel**.

Then you have to enter your current OTP (called TOTP in section 2-Factor Authentication):

After entering your password you see the welcome page of bwUniCluster 2.0 with the Message of the Day followed by a shell with prompt ("Eingabeaufforderung"):

Das Bild zeigt eine erfolgreiche SSH-Anmeldung auf dem bwUniCluster2.

Zu sehen ist die typische ASCII-Art-Begrüßung:

bwUniCluster2
(KITE 2.0, RHEL 8.2, Lustre 2.12.6_ddn40)

Darunter stehen Informationen und Links:

- Wiki: <https://wiki.bwhpc.de/e/bwUniCluster_2.0>  
- Ticket system: <https://www.bwhpc.de/supportportal>  
  E-Mail: <bwunicluster@bwhpc.de>  
- Training: <https://training.bwhpc.de>  
  E-Mail: <training@bwhpc.de>  

Es folgt der Hinweisbereich mit Lizenzinformation für Mannheim-Nutzer (Mathematica läuft aus) und Standort-News.

Am Ende sieht man den Login-Prompt etwa in der Form:
`[st_acXXXXX@uc2n995 ~]$`

You are in your home directory $HOME. An introduction for beginners ("What can I do now?") is given in the Linux section.

If you have logged into bwUniCluster 2.0 for the first time, you may try the following commands:

ls means "list" and shows the files in and subdirectories of your home directory. But there are no ones.

Try ls -a instead. This command lists all files, also the hidden ones.

Make a subdirectory "test" with the command mkdir test and check its existence with ls.

Now, you may want to go into the new subdirectory: Use the command cd test. "cd" means "change directory".

pwd is an abbreviation of "print working directory" and shows you the path to the current directory. /home/st/st_us-403340/st_ac117776/ is the path to my home directory.

With the command exit you close the shell and logout.

More useful basic commands are presented on the next page.

#### Logging in via PuTTY

Login via PuTTY is depreciated because PuTTY does NOT provide means to display GUIs natively. Use MobaXterm instead!

In the following screencast, Denis Grützner (Universität Heidelberg) explains PuTTY.

Putty – Skript zum Videotutorial
Denis Grützner (Universitätsrechenzentrum Heidelberg)
Hallo,
in diesem kurzen Video will ich Ihnen zeigen, wie Sie sich in Putty mit einem SSH-Server verbinden können. In
unserem Fall verbinden wir uns zum bwUniCluster.
Putty ist eine freie Software zum Herstellen von Verbindungen über Secure Shell, Telnet, Remote Login oder
seriellen Schnittstellen.
Dabei dient Putty als Client und stellt die Verbindung zu einem Server her. Putty ist für Windows und Linux
verfügbar.
In einer Terminalsitzung können befehle abgesetzt werden, die auf dem fernen System ausgeführt werden.
Die Arbeit mit graphischen Anwendungen ist nur möglich, wenn auf dem klienten ein X-Server installiert ist.
Fangen wir mal an:
Zuerst starten wir Putty und es erscheint die Puttykonfiguration.
Bei Hostname müssen Sie den vollständigen Namen oder die IP Adresse des Servers eintragen. Der Benutzername
kann mit einem @ voran gestellt werden
Wir verbinden uns mal zum bwUniCluster. Was man eingeben muss, zeige ich ihnen jetzt:
Zuerst müssen Sie das Kürzel ihrer Heimatuni eingeben:
Sind sie beispielsweise Angehöriger der Universität Heidelberg, so lautet ihr Kürzel “hd“ Wenn sie das Heimatkürzel
eingetragen haben, folgt ein “_“.
Danach folgt ihr Nutzername
Nach dem Nutzernamen folgt ein @-Zeichen danach folgt die Adresse des bwUniClusters: bwunicluster.scc.kit.edu
Der Port bleibt 22.
Wenn sie fertig sind, klicken sie auf „Open“.
Wenn man sich erstmals mit einem bisher unbekannten Server verbindet, zeigt die Kommandozeile den
Fingerabdruck des Serverzertifikates an.
Hiermit kann man sicherstellen, dass man nicht mit dem falschen Server verbunden ist, wie es z.B. bei einem „ManIn-The-Middle Angriff“ passieren könnte.
Beim ersten Anmelden bestätigt man diese Information einfach, wobei Putty sie für zukünftige Verbindungen
speichert.
Hier muss man sich jetzt mit seinem Dienstpasswort anmelden.
Wenn man sich mit seinem Dienstpasswort angemeldet hat, erscheinen die Login-Meldungen des bwUniClusters.
Auf der Kommandozeile kann man nun Befehle eingeben.
Wenn wir den Befehl „ls“ eingeben, zeigt uns das Terminal die Dateien, die auf dem Cluster drauf sind. Hier dürften
jetzt noch keine Dateien auf dem Cluster drauf sein.
Wie man Dateien auf den Cluster kopiert, sehen sie im nächsten Kapitel.

#### Another guidance (PuTTY)

Login via PuTTY is depreciated because PuTTY does NOT provide means to display GUIs natively. Use MobaXterm instead!

First, you have to install PuTTY and to configure it:
Das Bild zeigt die PuTTY-Konfigurationsoberfläche.

Im Bereich „Session“ sind folgende Einstellungen sichtbar:

- Host Name (or IP address): `ho_amuster@uc1.scc.kit.edu`
- Port: 22
- Connection type: SSH (ausgewählt)

Unter „Saved Sessions“ ist „bwUniCluster“ sowie „Default Settings“ zu sehen.

Unten befinden sich die Buttons:

- Open
- Cancel
- Save
- Load
- Delete

Links befindet sich der übliche Kategorienbaum (Session, Logging, Terminal, Window, Connection, etc.).
Das Bild zeigt ein PuTTY-Terminalfenster während des Logins.

Angezeigt wird:

login as: ho_amuster  
<ho_amuster@uc1.scc.kit.edu>'s password: █

Es wartet auf die Passworteingabe.

A new terminal window opens and you have to enter your password:

Finally, you have to add the host key:

Das Bild zeigt ein PuTTY-Sicherheitswarnfenster („PuTTY Security Alert“).

Textinhalt:

- Hinweis, dass der Host-Key des Servers nicht im lokalen Registry-Cache gespeichert ist.
- Es gibt keine Garantie, dass der Server wirklich der ist, für den man ihn hält.
- Der Fingerprint des Server-Keys wird angezeigt:
  `ssh-rsa 2048 52:d7:c2:79:78:b4:b6:ed:c0:1b:e9:57:05:91:50:88`
- Drei Optionen werden angeboten:
  - **Yes**: Den Host-Key akzeptieren und speichern.
  - **No**: Nur diesmal verbinden, ohne Speichern des Keys.
  - **Cancel**: Verbindung abbrechen.

Rechts unten befinden sich die Buttons **Yes**, **No**, **Cancel**.

and you are in your home directory and see the welcome message:

Das Bild zeigt ein erfolgreiches Login auf dem bwUniCluster.

Ablauf und Inhalte:

- Prompt zeigt: `login as: yc8563`
- Danach Passwortabfrage: `yc8563@bwunicluster.scc.kit.edu's password:`
- Anzeige des letzten Logins:  
  `Last login: Sun Feb 16 10:10:29 2014 from openvpn-cl-200-232.scc.kit.edu`

Es folgt der typische Begrüßungsblock des Clusters mit ASCII-Art:

bwUniCluster  
(KITE 2.0 / RHEL6.4 / Lustre 2.4.1)

Unterhalb stehen Hinweise und Links:

- Nutzer-Wiki: <https://www.bwhpc-c5.de/wiki/index.php/bwUniCluster_User_Guide>
- Hotline: <bwunicluster-hotline@lists.kit.edu>

Darunter ein Bereich „KIT News“ mit Datum (2014-02-06) und Ankündigung eines Seminars über bwHPC/bwUniCluster am 19. Februar 2014 inklusive Link.

Unten sieht man den aktiven Prompt:
`[Feb-16 10:12] yc8563@uc1n996:~$`

#### FAQ: "I cannot login. Why?"

Login at the registration server of your cluster, e.g. for the bwUniCluster 2.0 at <https://bwidm.scc.kit.edu>.

The following screenshot shows the page where you can see with which services you are already registered and which services are available:
Die Seite zeigt das KIT-Portal „Föderierte Dienste am KIT“.

Bereich: **You have already registered with the following services:**

1. **bwUniCluster 2.0**  
   Beschreibung: vom SCC betriebenes Hochleistungsrechnersystem für Universitäten und Hochschulen in Baden-Württemberg.  
   Links:
   - Service description
   - Registry info
   - Set service password
   - Set SSH Key

2. **bwSync&Share**  
   Beschreibung: Online-Speicherdienst, ermöglicht Datenaustausch und Synchronisation zwischen Geräten, Teil der LSDF am KIT.  
   Links:
   - Service description
   - Registry info

Darunter:

**The following services are available:**

- **JUSTUS 2**  
  bwForCluster für Computational Chemistry und Quantum Sciences an der Uni Ulm.  
  Links:
  - Service description
  - Register

Am unteren Rand Hinweis: Man soll für Details „Registry info“ anklicken und zum Registrieren „Register“.

Registered services
If bwUniCluster 2.0 is not shown at all, you have not got the entitlement of your university. Return to Step A on the bwUniCluster 2.0 registration page!

If bwUniCluster 2.0 is shown under "The following services are available:", register yourself.

If you are already registered with the bwUniCluster 2.0, check the info given at "Registry info" as well as at "Index" and "Personal data" as shown in the figures below.

Das Bild zeigt den Abschnitt „bwUniCluster 2.0“ aus dem KIT-Portal.

Zu sehen ist eine Beschreibung des bwUniCluster 2.0 als vom SCC betriebenes Hochleistungsrechnersystem für Universitäten und Hochschulen in Baden-Württemberg.

Darunter befinden sich vier Links, jeweils mit kleinem Icon:

- Service description  
- **Registry info** (gelb markiert)  
- Set service password  
- Set SSH Key

Registration info

Index and Personal data
Check, if you filled out the questionnaire (Step C) within 14 days after your registration!

## 8 Linux

### Introduction: Shells and Your Home Directory

Working with Linux means entering commands in a shell.

If you have logged into bwUniCluster 2.0 for the first time, you may try the following commands:

Das Bild zeigt ein geöffnetes SSH-Terminal auf dem bwUniCluster2 innerhalb eines Windows-Terminalprogramms (mit Menüleiste: Games, Settings, Macros, Help).

Inhalt im Terminal:

- Begrüßung mit ASCII-Art „bwUniCluster2“
- Links zu Wiki, Ticket-System und Training
- Hinweis für Mannheim-Nutzer (Mathematica-Lizenz)
- Danach der Prompt:

`[st_ac117776@uc2n995 ~]$ ls`  
→ Ausgabe: `.bash_history  .bash_profile  .cache  .dbus  .esd_auth  .kshrc  .mozilla  .Xauthority .bash_logout .bashrc .config .emacs .gnome2 .local .wget-hsts .zshrc`

`mkdir test`

`ls`  
→ Ausgabe: `test`

`cd test`

`pwd`  
→ Ausgabe: `/home/st/st_us-403340/st_ac117776/test`

Der Nutzer befindet sich nun im neu erstellten Verzeichnis `test`.

ls means "list" and shows the files in and subdirectories of your home directory. But there are no ones.

Try ls -a instead. This command lists all files, also the hidden ones.

Make a subdirectory "test" with the command mkdir test and check its existence with ls.

Now, you may want to go into the new subdirectory: Use the command cd test. "cd" means "change directory".

pwd is an abbreviation of "print working directory" and shows you the path to the current directory. /home/st/st_us-403340/st_ac117776/ is the path to my home directory.

With the command exit you close the shell and logout.

More useful basic commands are presented on the next page.

### Basic Commands

The following table shows basic Linux commands:

| Befehl                           | Beschreibung                   |
|----------------------------------|--------------------------------|
| `$ pwd`                          | show path of working directory |
| `$ mkdir <dirname>`              | make directory                 |
| `$ ls -l`                        | list directory contents        |
| `$ cd`                           | change directory               |
| `$ cp <sourcefile> <targetfile>` | copy file                      |
| `$ mv <sourcefile> <targetfile>` | move file                      |
| `$ rm <filename>`                | remove file                    |
| `$ man <command>`                | show command's manual          |
| `$ vi`                           | standard unix editor           |

#### Links to more Linux commands and editors

Learn Shell
<http://www.learnshell.org/de/>

Unix and Linux Tips
<http://www.computerhope.com/unix.htm>

Linux for beginners
<https://www.tutorialspoint.com/unix/unix-directories.htm>

      Bash-Scripting
shell scripting-1
<http://tldp.org/HOWTO/Bash-Prog-Intro-HOWTO.html>

shell scripting 2
<http://www.tldp.org/LDP/abs/html/varsubn.html>

Editor
Nano
<http://wikipedia.org/wiki/Nano_(Texteditor)>

cheat sheet nano
<http://alturl.com/wbtrk>

VIM
<http://www.wikipedia.org/wiki/Vim>

cheat sheet VIM
<http://vim.rtorr.com/>

cheat sheet emacs
<http://www.rgrjr.com/emacs/emacs_cheat.html>

       Video
Video Editor VIM - interaktiv

## 9 Data Transfer

### Data Transfer: Linux

You can transfer files between your PC and a cluster you have access to by using the commands scp or sftp:

| Befehl                                      | Beschreibung                                   |
|---------------------------------------------|------------------------------------------------|
| `$ scp <sourcefile> <targetfile>`           | secure copy (remote file copy program)         |
| `$ scp -r <sourcedir> <targetdir>`          | recursively copy entire directories            |
| `$ sftp <targetdir>`                         | secure file transfer program                   |
| `$ put \| get <sourcefile>`                 | upload/download file                           |

Commands for file transfer.
Example scp:
In order to copy the file paket.tar from your PC to the subdirectory dir of your home directory on the bwUniCluster 2.0, type the following command in the directory where paket.tar is stored and subsequently enter your TOTP and your password:
$ scp paket.tar <ab1234@uc2.scc.kit.edu>:dir/
Your OTP:
Password:

Example scp:
Das Bild zeigt ein Terminal unter Ubuntu (baerbel@baerbel-VirtualBox).

Der ausgeführte Befehl:

`scp testfile st_ac117776@uc2.scc.kit.edu:.`

Darunter erscheinen:

- Eingabeaufforderung für OTP: `Your OTP: 840616`
- Passworteingabe: `Password:`
- Übertragungsstatus: `testfile`  
  Fortschritt: `100%` – 12 Bytes – 0.2KB/s – 00:00

Die Datei **testfile** wurde erfolgreich auf den Cluster kopiert.

Example sftp:
In order to put the file paket.tar into the subdirectory dir of your home directory on the bwUniCluster 2.0, first establish a sftp connection to the target directory and enter your TOTP and your password:
$ sftp ab1234@uc2.scc.kit.edu:dir
Your OTP:
Password:
Connected to uc2.scc.kit.edu.
Changing to: ${HOME}/dir
sftp>

Then, inside the sftp shell, type the command
sftp> put paket.tar

Hint: The user name ab1234 and the hostname uc2.scc.kit.edu are explained on the page Login: Linux User.

Example sftp:
Das Bild zeigt ein Ubuntu-Terminal (baerbel@baerbel-VirtualBox) beim Datei-Upload per SFTP.

Ablauf:

`ls`  
→ zeigt Verzeichnisse und die Datei *testfile*

`sftp st_ac117776@uc2.scc.kit.edu:`  

- OTP-Abfrage: `Your OTP: 155919`
- Passwortabfrage: `Password:`
- Verbindung: `Connected to uc2.scc.kit.edu.`
- Automatischer Wechsel in das Home-Verzeichnis:  
  `Changing to: /pfs/data5/home/st/st_us-403340/st_ac117776/.`

`sftp> put testfile`  

- Hochladen der Datei in das Cluster-Home  
- Fortschritt: `testfile 100% 12 0.6KB/s 00:00`

`sftp> exit`  
→ Rückkehr ins lokale Terminal.

Die Datei **testfile** wurde erfolgreich hochgeladen.

In the following screencast, Christian Greiner explains data transfer with scp.

Video Player

00:00
02:01

"Datentransfer zum bwUniCluster" (SCP) by Christian Greiner (Universität Heidelberg).
Video Player

00:00
02:26

Möchten sie ihre Daten zwischen ihrem lokalen Rechner und dem Server bzw. einem anderen
Rechner austauschen, dann wird der Befehl SCP, der für „Secure Copy“ steht, benötigt. SCP
sendet Daten verschlüsselt über eine SSH-Verbindung.
Hierbei werden alle Befehle vom lokalen Arbeitsplatz ausgeführt.

1. Senden einer Datei vom Arbeitsplatz zum Server
Zunächst möchten wir eine Datei von unserem Arbeitsplatz zum Server kopieren.
Der Befehl ist wie folgt aufgebaut:
1. scp (Danach wird immer die Quelle (von wo) und danach das Ziel (wohin) angegeben)
2. Quelldatei (die Datei, sowie deren Pfad, die sie kopieren möchten. )
3. Angabe des Zielrechners:
a. Benutzername (genau wie beim SSH-Befehl mit HD_ID) @ bwunicluster.scc.kit.edu
4. :Zieldatei ( Pfad und Name der Quelldatei nach dem Doppelpunkt angeben
Zuletzt bestätigen sie ihre Aktion mit ihrem Dienstpasswort.
Das Terminal zeigt sofort den Übertragungsstatus der Datei an.
(Pause -> Warten bis fertig geladen)
Daran sieht man nun, dass die Datei erfolgreich auf den bwUniCluster kopiert wurde.
2. Holen einer Datei vom Server zum Arbeitsplatz
Um eine Datei vom bwUniCluster auf ihren Arbeitsrechner zu kopieren, wird der selbe Befehlt mit
vertauschen Argumenten verwendet.(Pause)
 Geben sie folgendes ein:
1. scp
2. Danach die Quelldatei, die sich auf dem Server befindet.(danach die Datei, sowie deren Pfad,
die sie kopieren möchten. -> Benutzername(mit HD_ID)@bwunicluster.scc.kit.edu: Quelldatei
3. Pfad und Zieldatei auf ihrem Arbeitsrechner
3. Ordnerinhalt Rekursiv Kopieren
Um einen kompletten Ordnerinhalt kopieren zu können, wird der Parameter „–r“ benötigt, der nach
dem bereits bekannten Befehl SCP folgt. Hierbei werden rekursiv alle Daten im Ordner auf dem
Zielrechner kopiert.
(Bsp -> Bilder zeigen)
Daten kopieren mit SCP – Script zum Videotutorial
Christian Greiner (Universitätsrechenzentrum Heidelberg)
4. Daten und Verzeichnisse abgleichen mit rysnc
Möchten sie ihre Daten, sowie die Verzeichnisstruktur von ihrem Arbeitsplatz mit dem
Server abgleichen, dann können sie den Befehl „rsync“ verwenden.
Das Programm rsync vergleicht die Größe, sowie das letzte Änderungsdatum der jeweiligen
Dateien und spiegelt diese nur dann, wenn auch wirklich eine Änderung an den Dateien
stattgefunden hat.
Um ihnen dies zu demonstrieren, befindet sich ein Ordner namens „Bilder“ auf
meinem Arbeitsrechner. Den Inhalt möchte ich nun mit dem Server spiegeln.
Der Befehl wird folgendermaßen ausgeführt:
rsync, danach der Parameter –avP.
 Hierbei steht das „a“ für Archive, was versucht die Metainformationen der Daten zu erhalten.
 Das v steht für „verbose“. Dadurch werden zusätzliche Informationen angezeigt.

Das „groß P“ steht für „pacial und progress“. Damit wird festgelegt, dass bei einem
Verbindungsabbruch die schon übertragenen Daten nicht gelöscht werden und, dass
der Übertragungsstatus angezeigt wird.
Optimal kann der Paramter „-z“ verwendet werden, um die Dateien zu komprimieren.
Nun geben sie ihr Dienstpasswort ein. Danach sehen sie eine Liste der übertragenen Daten.
Im dem Server-Ordner Bilder befinden sich jetzt alle von mir übermittelten Dateien.
Als nächstes erstelle ich eine Textdatei, die ich nachträglich mit dem Server spiegeln möchte.
Diese befindet sich ebenfalls im Bilder-Ordner auf meinem Arbeitsrechner.
Jetzt gebe ich denselben Befehl für das Spiegeln mit dem Server wie zuvor ein.
Danach zeigt mir die Kommandozeile an, dass nur die von mir neu erstellte Textdatei
übertragen wurde und die restlichen sich im Ordner befindlichen Dateien ignoriert
wurden.
 Genau wie beim SCP Befehl muss zuerst die Quelle dann das Ziel angegeben werden.

Part 3 (recursive copy with scp) and part 4 (rsync) of the screencast "Datentransfer zum bwUniCluster" by Christian Greiner (Universität Heidelberg).

### Data Transfer: Windows

We strongly recommend to use MobaXterm instead of WinSCP for data transfer between your PC and a cluster you have acess to.
<https://mobaxterm.mobatek.net/>

The login process with MobaXterm is explained on the page Login: Windows User. Make sure that you specify the SSH-browser type "SCP":

Das Bild zeigt erneut die Session-Einstellungen eines SSH-Clients.

**Basic SSH settings**

- Remote host: `uc2.scc.kit.edu` (gelb markiert)
- Specify username: aktiviert, Benutzername: `st_ac123456` (gelb markiert)
- Port: 22

**Advanced SSH settings**

- X11-Forwarding: aktiviert
- Compression: aktiviert
- Remote environment: „Interactive shell“
- SSH-browser type: „SCP (normal speed)“ (gelb markiert)
- Use private key: deaktiviert

Unten Buttons: **OK** (grün markiert) und **Cancel**.

Then, you can copy files between your Windows system and bwUniCluster 2.0 by Drag&Drop.

When copying directories and files from Windows to a Linux system, always check the access rights!

See the page Access Rights and Access Control for more information.

#### Data Transfer with WinSCP (deprecated)

You can transfer files between your PC and a cluster by using WinSCP. In the following WinSCP is explained.

Start WinSCP:

and transfer the files by drag&drop:

In the following screencast, Denis Grützner (Universität Heidelberg) explains WinSCP.

Video Player

00:00
02:39
Data Transfer with WinSCP (deprecated)
You can transfer files between your PC and a cluster by using WinSCP. In the following WinSCP is explained.

Start WinSCP:

and transfer the files by drag&drop:

In the following screencast, Denis Grützner (Universität Heidelberg) explains WinSCP.

Video Player

00:00
02:39

Hallo,
in diesem Kapitel möchte ich Ihnen zeigen, wie man Daten zum bwUniCluster
transferiert. Hierzu benötigt man das Programm WinSCP (Windows Secure Copy).
WinSCP ermöglicht einen geschützen Datentransfer zwischen verschiedenen Rechnern.
Der Vorteil ist, dass die Daten verschlüsselt sind und sie daher auch kein Dritter mitlesen kann. Der
Benutzer hat hier noch die Auswahl zu entscheiden, welche Oberfläche er nutzen will.
Es gibt 2 verschieden Varianten von Oberflächen:
Zu einem gibt es den Norton Commander, den ich ausschließlich in diesem Video demonstrieren werde.
Hier werden das lokale und das entfernte Dateisystem in einem einzigen Fenster gegenüber gestellt.
Zum anderen kann man den Windows Explorer verwenden. Bei dieser Ansicht öffnen sich 2 Fenster, je eins
für das lokale und eins für das entfernte Dateisystem, zwischen denen man Datein verschieben kann.
WinSCP steht unter der GNU GPL, dies ist eine OpenSource License, daher ist das Programm kostenfrei. Fangen
wir mal an:
Der Rechnername ist die IP Adresse oder der vollständige Name des Servers zu dem man sich verbinden will.
In unserem Fall verbinden wir uns zum BWUniCluster. Wir geben die Adresse des bwUniClusters ein:
„bwunicluster.scc.kit.edu“
Nun geben sie Ihren Benutzernamen ein, dieser setzt sich zusammen aus dem Kürzel ihrer Heimatuni
und dem dazugehörigen Nutzernamen. Sind sie beispielsweise Angehöriger der Universität
Heidelberg, muss vor ihrer allgemeinen Nutzerkennung „hd_“ stehen.
Bei Kennwort müssen Sie ihr Dienstpasswort eintragen, das Sie bei der Registrierung gesetzt haben.
Wenn man seine Benutzerdaten eingetragen hat, kann man entscheiden ob man sie speichern
will oder sich direkt anmeldet.
Wir melden uns mal an.
WinScp – Skript zum Videotutorial
Denis Grützner (Universitätsrechenzentrum Heidelberg)
1
Auch hier wird bei der ersten Verbindung der Fingerabdruck des Serverzertifikates angezeigt.
Wir bestätigen wieder mit „ja“.
Auch hier wird bei der ersten Verbindung der Fingerabdruck des Serverzertifikates angezeigt.
Wir bestätigen wieder mit „ja“.
So ich habe hier schon mal ein Testdokument vorbereitet und werde es jetzt mal auf den Server kopieren.
Das Ganze müssen wir mit „ok“ bestätigen.
Jetzt haben wir das Testdokument auf den BWUni-Cluster erfolgreich kopiert.
Wenn wir jetzt wieder auf Putty gehen und jetzt „ls“ eingeben, wird dasTestdokument.txt
angezeigt. Ich hoffe ich konnte ihnen weiterhelfen.
Bis zum nächsten mal.
"Datentransfer zum bwUniCluster" (WinSCP) by Denis Grützner (Universität Heidelberg).

## 10 Hardware and Architecture

### Architecture of a HPC Cluster

Architecture of a HPC Cluster
All HPC clusters are composed of login nodes, compute nodes and parallel storage systems connected by fast data networks, and thus have a similar structure. In this chapter, I explain this using the example of the bwUniCluster (as of 2016).

Die Grafik zeigt die Hardware-Architektur eines HPC-Clusters mit InfiniBand 4X FDR als zentralem Hochgeschwindigkeitsnetzwerk.

Oben:

- Mehrere Produktionsknoten (rot), teils mit **16×**- und **32×**-Konfigurationen.
- Zwei Kategorien sind hervorgehoben:  
  - **Production nodes with 64 GB main memory**  
  - **Production nodes with 1 TB main memory**
- Über jedem Block befinden sich Festplatten- bzw. Speicher-Symbole.

Mitte:

- Ein großer grüner Balken: **InfiniBand 4X FDR** (zentrales Interconnect-Netz).
- Von dort führen Verbindungen zu verschiedenen Knotengruppen und Speichersystemen.

Unten links:

- **Login Nodes** (gelb, jeweils **16×**) mit Stapeln von Festplatten-/Nutzersymbolen.
- **Service Nodes** (violett, **16×**) mit einzelnen Speichersymbolen.

Unten rechts:

- Speicherbereiche, angebunden über InfiniBand (grüne Boxen):
  - Mehrere **InfiniBand**-Einheiten führen zu jeweils **8×** Storage-Knoten.
  - Links: **$HOME** (z. B. Benutzer-Homeverzeichnisse)
  - Rechts: **$WORK Workspaces** (Arbeitsverzeichnisse für rechenintensive Jobs)

Die Architektur zeigt ein klassisches HPC-Layout:

- Rechenknoten oben  
- Service- und Login-Knoten unten links  
- Zentrale Storage-Systeme unten rechts  
- Alles über InfiniBand verbunden.

Figure 1: The architecture of the bwUniCluster (until 2016).
The cluster users log in on one of the two login nodes (also called front-ends, yellow in Figure 1) and have access to their home directories $HOME and working directories (blue in Figure 1) stored in the parallel file system Lustre.
The working directories are called workspaces. The working directories $WORK are deprecated on bwUniCluster 2.0.

Usually, there are different kinds of compute nodes (production nodes, red in Figure 1). The bwUniCluster has a lot of "thin" nodes equipped with 64 GB main memory and consisting of two 8-core processors (16x), and some "fat nodes", each with 1 TB main memory and consisting of four 8-core processors (32x). Both, thin nodes and fat nodes, are Intel Sandy Bridge processors. Since May 2017, there are also nodes equipped with Intel Broadwell processors, not shown in Figure 1. All compute nodes have their own local hard disks.

The compute nodes are accessible only via the batch system.

On the login nodes, you can do
short compilations of your program codes and
short pre- and postprocessing of your batch jobs.
But you must not run your compute jobs on the login nodes!

See the bwHPC Wiki for more information.
The login nodes, the compute nodes, the service nodes for the administrators (purple in Figure 1) and the storage systems are connected by a fast InfiniBand network (green in Figure 1).

The following table summarizes the main features of the bwUniCluster's nodes (as at October 2017).

|                                  | Compute nodes "Thin" | Compute nodes "Fat" | Compute nodes "Broadwell" | Login nodes "Thin / Fat" | Login nodes "Broadwell" | Service nodes |
|----------------------------------|-----------------------|----------------------|----------------------------|---------------------------|---------------------------|---------------|
| **Number of nodes**             | 512                   | 8                    | 352                        | 2                         | 2                         | 10            |
| **Processors**                  | Intel Xeon E5-2670 (Sandy Bridge) | Intel Xeon E5-4640 (Sandy Bridge) | Intel Xeon E5-2660 v4 (Broadwell) | Intel Xeon E5-2670 (Sandy Bridge) | Intel Xeon E5-2630 v4 (Broadwell) | Intel Xeon E5-2670 (Sandy Bridge) |
| **Processor frequency (GHz)**   | 2.6                   | 2.4                  | 2.0                        | 2.6                       | 2.2                       | 2.6           |
| **Number of sockets**           | 2                     | 4                    | 2                          | 2                         | 2                         | –             |
| **Total number of cores**       | 16                    | 32                   | 28                         | 16                        | 20                        | 16            |
| **Main memory**                 | 64 GB                 | 1024 GB              | 128 GB                     | 64 GB                     | 128 GB                    | 64 GB         |
| **Local disk**                  | 2 TB                  | 7 TB                 | 480 GB                     | 4 TB                      | 480 GB                    | 1 TB          |
| **Cache per socket**            | Level 1: 8×64 KB<br>Level 2: 8×256 KB<br>Level 3: 20 MB | Level 1: 8×64 KB<br>Level 2: 8×256 KB<br>Level 3: 20 MB | Level 1: 8×64 KB<br>Level 2: 8×256 KB<br>Level 3: 35 MB | Level 1: 8×64 KB<b

Figure 2: Components of the bwUniCluster (as at October 2017).

Example: Broadwell nodes
The Intel Xeon E5-2660 v4 (Broadwell) processor is a multicore CPU with 14 cores. Its frequency is 2 GHz, and it has Level 1, Level 2 and Level 3 caches. Knowing the sizes of the caches is important, when you want to optimize the performance of your software.
Two Broadwell processors together build a compute node: It is a two-socket system with 28 cores and 128 GB main memory (shared memory), connected to a local disk (480 GB).
There are 352 of these Broadwell compute nodes. They are connected among themselves and to the other nodes by an InfiniBand 4X FDR interconnect.

#### BwUniCluster2.0/Hardware and Architecture

< BwUniCluster2.0
(Redirected from BwUniCluster 2.0 Hardware and Architecture)
Jump to navigationJump to search

Contents
1 Architecture of bwUniCluster 2.0
2 Components of bwUniCluster
3 File Systems
3.1 Selecting the appropriate file system
3.2 $HOME
3.3 Workspaces
3.3.1 Reminder for workspace deletion
3.3.2 Restoring expired Workspaces
3.3.3 Linking workspaces in Home
3.4 Improving Performance on $HOME and workspaces
3.4.1 Improving Throughput Performance
3.4.2 Improving Metadata Performance
3.5 Workspaces on flash storage
3.5.1 Advantages of this file system
3.5.2 Access restrictions
3.5.3 Using the file system
3.6 $TMPDIR
3.6.1 Usage example for $TMPDIR
3.7 LSDF Online Storage
3.8 BeeOND (BeeGFS On-Demand)
3.9 Backup and Archiving
Architecture of bwUniCluster 2.0
The bwUniCluster 2.0 is a parallel computer with distributed memory. Each node of system consists of at least two Intel Xeon processor, local memory, disks, network adapters and optionally accelerators (NVIDIA Tesla V100, A100 or H100). All nodes are connected by a fast InfiniBand interconnect. In addition the file system Lustre, that is connected by coupling the InfiniBand of the file server with the InfiniBand switch of the compute cluster, is added to bwUniCluster 2.0 to provide a fast and scalable parallel file system.

The operating system on each node is Red Hat Enterprise Linux (RHEL) 8.4. A number of additional software packages like e.g. SLURM have been installed on top. Some of these components are of special interest to end users and are briefly discussed in this document. Others which are of greater importance to system administrators will not be covered by this document.

The individual nodes of the system may act in different roles. According to the services supplied by the nodes, they are separated into disjoint groups. From an end users point of view the different groups of nodes are login nodes, compute nodes, file server nodes and administrative server nodes.

Login Nodes

The login nodes are the only nodes that are directly accessible by end users. These nodes are used for interactive login, file management, program development and interactive pre- and postprocessing. Three nodes are dedicated to this service but they are all accessible via one address and a DNS round-robin alias distributes the login sessions to the different login nodes.

To prevent login nodes from being used for activities that are not permitted there and that affect the user experience of other users, long-running and/or compute-intensive tasks are periodically terminated without any prior warning. Please refer to Allowed Activities on Login Nodes.

Compute Node

The majority of nodes are compute nodes which are managed by a batch system. Users submit their jobs to the SLURM batch system and a job is executed when the required resources become available (depending on its fair-share priority).

File Server Nodes

The hardware of the parallel file system Lustre incorporates some file server nodes; the file system Lustre is connected by coupling the InfiniBand of the file server with the independent InfiniBand switch of the compute cluster. In addition to shared file space there is also local storage on the disks of each node (for details see chapter "File Systems").

Administrative Server Nodes

Some other nodes are delivering additional services like resource management, external network connection, administration etc. These nodes can be accessed directly by system administrators only.

Components of bwUniCluster
Compute nodes "Thin" Compute nodes "HPC" Compute nodes "Ice Lake" Compute nodes "Fat" GPU x4 GPU x8 Ice Lake + GPU x4 Login
Number of nodes 200 + 60 260 272 6 14 10 15 3
Processors Intel Xeon Gold 6230 Intel Xeon Gold 6230 Intel Xeon Platinum 8358 Intel Xeon Gold 6230 Intel Xeon Gold 6230 Intel Xeon Gold 6248 Intel Xeon Platinum 8358
Number of sockets 2 2 2 4 2 2 2 2
Processor frequency (GHz) 2.1 Ghz 2.1 Ghz 2.6 Ghz 2.1 Ghz 2.1 Ghz 2.6 Ghz 2.5 Ghz
Total number of cores 40 40 64 80 40 40 64 40
Main memory 96 GB / 192 GB 96 GB 256 GB 3 TB 384 GB 768 GB 512 GB 384 GB
Local SSD 960 GB SATA 960 GB SATA 1,8 TB NVMe 4,8 TB NVMe 3,2 TB NVMe 15 TB NVMe 6,4 TB NVMe
Accelerators - - - - 4x NVIDIA Tesla V100 8x NVIDIA Tesla V100 4x NVIDIA A100 / 4x NVIDIA H100 -
Accelerator memory - - - - 32 GB 32 GB 80 GB / 94 GB -
Interconnect IB HDR100 (blocking) IB HDR100 IB HDR200 IB HDR IB HDR IB HDR IB HDR200 IB HDR100 (blocking)
Table 1: Properties of the nodes

File Systems
On bwUniCluster 2.0 the parallel file system Lustre is used for most globally visible user data. Lustre is open source and Lustre solutions and support are available from different vendors. Nowadays, most of the biggest HPC systems are using Lustre. An initial home directory on a Lustre file system is created automatically after account activation, and the environment variable $HOME holds its name. Users can create so-called workspaces on another Lustre file system for non-permanent data with temporary lifetime. There is another workspace file system based on flash storage for special requirements available.

Within a batch job further file systems are available:

The directory $TMPDIR is only available and visible on the local node. It is located on fast SSD storage devices.
On request a parallel on-demand file system (BeeOND) is created which uses the SSDs of the nodes which were allocated to the batch job.
On request the external LSDF Online Storage is mounted on the nodes which were allocated to the batch job. This file system is based on the parallel file system Spectrum Scale.
Some of the characteristics of the file systems are shown in Table 2.

Property $TMPDIR BeeOND $HOME Workspace Workspace
on flash
Visibility local node nodes of batch job global global global
Lifetime batch job runtime batch job runtime permanent max. 240 days max. 240 days
Disk space 960 GB - 6.4 TB
details see table 1 n*750 GB 1.2 PiB 4.1 PiB 236 TiB
Capacity Quotas no no yes
1 TiB per user, for
MA users 256 GiB
also per organization yes
40 TiB per user yes
1 TiB per user
Inode Quotas no no yes
10 million per user
for MA users 2.5 million yes
30 million per user yes
5 million per user
Backup no no yes no no
Read perf./node 500 MB/s - 6 GB/s
depends on type of local SSD / job queue:
520 MB/s @ single / multiple
800 MB/s @ multiple_e
6600 MB/s @ fat
6500 MB/s @ gpu_4
6500 MB/s @ gpu_8 400 MB/s - 500 MB/s
depends on type of local SSDs / job queue:
500 MB/s @ multiple
400 MB/s @ multiple_e 1 GB/s 1 GB/s 1 GB/s
Write perf./node 500 MB/s - 4 GB/s
depends on type of local SSD / job queue:
500 MB/s @ single / multiple
650 MB/s @ multiple_e
2900 MB/s @ fat
2090 MB/s @ gpu_4
4060 MB/s @ gpu_8 250 MB/s - 350 MB/s
depends on type of local SSDs / job queue:
350 MB/s @ multiple
250 MB/s @ multiple_e 1 GB/s 1 GB/s 1 GB/s
Total read perf. n*500-6000 MB/s n*400-500 MB/s 18 GB/s 54 GB/s 45 GB/s
Total write perf. n*500-4000 MB/s n*250-350 MB/s 18 GB/s 54 GB/s 38 GB/s
 global: all nodes of UniCluster access the same file system;
 local: each node has its own file system;
 permanent: files are stored permanently;
 batch job: files are removed at end of the batch job.
Table 2: Properties of the file systems

Selecting the appropriate file system
In general, you should separate your data and store it on the appropriate file system. Permanently needed data like software or important results should be stored below $HOME but capacity restrictions (quotas) apply. In case you accidentally deleted data on $HOME there is a chance that we can restore it from backup. Permanent data which is not needed for months or exceeds the capacity restrictions should be sent to the LSDF Online Storage or to the archive and deleted from the file systems. Temporary data which is only needed on a single node and which does not exceed the disk space shown in the table above should be stored below $TMPDIR. Data which is read many times on a single node, e.g. if you are doing AI training, should be copied to $TMPDIR and read from there. Temporary data which is used from many nodes of your batch job and which is only needed during job runtime should be stored on a parallel on-demand file system. Temporary data which can be recomputed or which is the result of one job and input for another job should be stored in workspaces. The lifetime of data in workspaces is limited and depends on the lifetime of the workspace which can be several months.

For further details please check the chapters below.

$HOME
The home directories of bwUniCluster 2.0 (uc2) users are located in the parallel file system Lustre. You have access to your home directory from all nodes of uc2. A regular backup of these directories to tape archive is done automatically. The directory $HOME is used to hold those files that are permanently used like source codes, configuration files, executable programs etc.

On uc2 there is a default user quota limit of 1 TiB and 10 million inodes (files and directories) per user. For users of University of Mannheim the limit is 256 GiB and 2.5 million inodes. You can check your current usage and limits with the command

$ lfs quota -uh $(whoami) $HOME
In addition to the user limit there is a limit of your organization (e.g. university) which depends on the financial share. This limit is enforced with so-called Lustre project quotas. You can show the current usage and limits of your organization with the following command:

lfs quota -ph $(grep $(echo $HOME | sed -e "s|/[^/]*/[^/]*$||") /pfs/data5/project_ids.txt | cut -f 1 -d\ ) $HOME
Workspaces
On uc2 workspaces can be used to store large non-permanent data sets, e.g. restart files or output data that has to be post-processed. The file system used for workspaces is also the parallel file system Lustre. This file system is especially designed for parallel access and for a high throughput to large files. It is able to provide high data transfer rates of up to 54 GB/s write and read performance when data access is parallel.

On uc2 there is a default user quota limit of 40 TiB and 30 million inodes (files and directories) per user. You can chek your current usage and limits with the command

$ lfs quota -uh $(whoami) /pfs/work7
Note that the quotas include data and inodes for all of your workspaces and all of your expired workspaces (as long as they are not yet completely removed).

Workspaces have a lifetime and the data on a workspace expires as a whole after a fixed period. The maximum lifetime of a workspace on uc2 is 60 days, but it can be renewed at the end of that period 3 times to a total maximum of 240 days after workspace generation.

Creating, deleting, finding, extending and sharing workspaces is explained on the workspace page.

Reminder for workspace deletion
Normally you will get an email every day starting 7 days before a workspace expires. You can send yourself a calender entry which reminds you when a workspace will be automatically deleted:

$ ws_send_ical <workspace> <email>
Restoring expired Workspaces
At expiration time your workspace will be moved to a special, hidden directory. On uc2 expired workspaces are currently kept for 30 days. During this time you can still restore your data into a valid workspace. The same is true for released workspaces but they are only kept until the next night. In order to restore an expired workspace, use

ws_restore -l
to get a list of your expired workspaces, and then restore them into an existing, active workspace (here with name my_restored):

ws_restore <full_name_of_expired_workspace> my_restored
NOTE: The expired workspace has to be specified using the full name as listed by ws_restore -l, including username prefix and timestamp suffix (otherwise, it cannot be uniquely identified). The target workspace, on the other hand, must be given with just its short name as listed by ws_list, without the username prefix.

NOTE: ws_restore can only work on the same filesystem. So you have to ensure that the new workspace allocated with ws_allocate is placed on the same filesystem as the expired workspace. Therefore, you can use -F <filesystem> flag if needed.

Linking workspaces in Home
It might be valuable to have links to personal workspaces within a certain directory, e.g. below the user home directory. The command

ws_register <DIR>
will create and manage links to all personal workspaces within in the directory <DIR>. Calling this command will do the following:

The directory <DIR> will be created if necessary
Links to all personal workspaces will be managed:
Creates links to all available workspaces if not already present
Removes links to released or expired workspaces
Improving Performance on $HOME and workspaces
The following recommendations might help to improve throughput and metadata performance on Lustre filesystems.

Improving Throughput Performance
Depending on your application some adaptations might be necessary if you want to reach the full bandwidth of the filesystems. Parallel filesystems typically stripe files over storage subsystems, i.e. large files are separated into stripes and distributed to different storage subsystems. In Lustre, the size of these stripes (sometimes also mentioned as chunks) is called stripe size and the number of used storage subsystems is called stripe count.

When you are designing your application you should consider that the performance of parallel filesystems is generally better if data is transferred in large blocks and stored in few large files. In more detail, to increase throughput performance of a parallel application following aspects should be considered:

collect large chunks of data and write them sequentially at once,
to exploit complete filesystem bandwidth use several clients,
avoid competitive file access by different tasks or use blocks with boundaries at stripe size (default is 1MB),
if files are small enough for the SSDs and are only used by one process store them on $TMPDIR.
With previous Lustre versions adapting the Lustre stripe count was the most important optimization. However, for the workspaces of uc2 the new Lustre feature Progressive File Layouts has been used to define file striping parameters. This means that the stripe count is adapted if the file size is growing. In normal cases users no longer need to adapt file striping parameters in case they have very huge files or in order to reach better performance.

If you know what you are doing you can still change striping parameters, e.g. the stripe count, of a directory and of newly created files. New files and directories inherit the stripe count from the parent directory. E.g. if you want to enhance throughput on a single very large file which is created in the directory $HOME/my_output_dir you can use the command

$ lfs setstripe -c-1 $HOME/my_output_dir
to change the stripe count to -1 which means that all storage subsystems of the file system are used to store that file. If you change the stripe count of a directory the stripe count of existing files inside this directory is not changed. If you want to change the stripe count of existing files, change the stripe count of the parent directory, copy the files to new files, remove the old files and move the new files back to the old name. In order to check the stripe setting of the file my_file use

$ lfs getstripe my_file
Also note that changes on the striping parameters (e.g. stripe count) are not saved in the backup, i.e. if directories have to be recreated this information is lost and the default stripe count will be used. Therefore, you should annotate for which directories you made changes to the striping parameters so that you can repeat these changes if required.

Improving Metadata Performance
Metadata performance on parallel file systems is usually not as good as with local filesystems. In addition, it is usually not scalable, i.e. a limited resource. Therefore, you should omit metadata operations whenever possible. For example, it is much better to have few large files than lots of small files. In more detail, to increase metadata performance of a parallel application following aspects should be considered:

avoid creating many small files,
avoid competitive directory access, e.g. by creating files in separate subdirectories for each task,
if many small files are only used within a batch job and accessed by one process store them on $TMPDIR,
change the default colorization setting of the command ls (see below).
On modern Linux systems, the GNU ls command often uses colorization by default to visually highlight the file type; this is especially true if the command is run within a terminal session. This is because the default shell profile initializations usually contain an alias directive similar to the following for the ls command:

$ alias ls="ls --color=tty"
However, running the ls command in this way for files on a Lustre file system requires a stat() call to be used to determine the file type. This can result in a performance overhead, because the stat() call always needs to determine the size of a file, and that in turn means that the client node must query the object size of all the backing objects that make up a file. As a result of the default colorization setting, running a simple ls command on a Lustre file system often takes as much time as running the ls command with the -l option (the same is true if the -F, -p, or the -classify option, or any other option that requires information from a stat() call, is used). To avoid this performance overhead when using ls commands, add an alias directive similar to the following to your shell startup script:

$ alias ls="ls --color=never"
Workspaces on flash storage
There is another workspace file system for special requirements available. The file system is called full flash pfs and is based on the parallel file system Lustre.

Advantages of this file system
All storage devices are based on flash (no hard disks) with low access times. Hence performance is better compared to other parallel file systems for read and write access with small blocks and with small files, i.e. IOPS rates are improved.
The file system is mounted on bwUniCluster 2.0 and HoreKa, i.e. it can be used to share data between these clusters.
Access restrictions
Only HoreKa users or KIT users of bwUniCluster 2.0 can use this file system.

Using the file system
As KIT or HoreKa user you can use the file system in the same way as a normal workspace. You just have to specify the name of the flash-based workspace file system using the option -F to all the commands that manage workspaces. On bwUniCluster 2.0 it is called ffuc, on HoreKa it is ffhk. For example, to create a workspace with name myws and a lifetime of 60 days on bwUniCluster 2.0 execute:

ws_allocate -F ffuc myws 60
If you want to use the full flash pfs on bwUniCluster 2.0 and HoreKa at the same time, please note that you only have to manage a particular workspace on one of the clusters since the name of the workspace directory is different. However, the path to each workspace is visible and can be used on both clusters.

Other features are similar to normal workspaces. For example, we are able to restore expired workspaces for few weeks and you have to open a ticket to request the restore. There are quota limits with a default limit of 1 TiB capacity and 5 millions inodes per user. You can check your current usage with

lfs quota -uh $(whoami) /pfs/work8
$TMPDIR
The environment variable $TMPDIR contains the name of a directory which is located on the local SSD of each node. This means that different tasks of a parallel application use different directories when they do not utilize the same node. Although $TMPDIR points to the same path name for different nodes of a batch job, the physical location and the content of this directory path on these nodes is different.

This directory should be used for temporary files being accessed from the local node during job runtime. It should also be used if you read the same data many times from a single node, e.g. if you are doing AI training. In this case you should copy the data at the beginning of your batch job to $TMPDIR and read the data from there, see usage example below.

The $TMPDIR directory is located on extremely fast local SSD storage devices. This means that performance on small files is much better than on the parallel file systems. The capacity of the local SSDs for each node type is different and can be checked in Table 1 above. The capacity of $TMPDIR is at least 800 GB.

Each time a batch job is started, a subdirectory is created on the SSD of each node and assigned to the job. $TMPDIR is set to the name of the subdirectory and this name contains the job ID so that it is unique for each job. At the end of the job the subdirectory is removed.

On login nodes $TMPDIR also points to a fast directory on a local SSD disk but this directory is not unique. It is recommended to create your own unique subdirectory on these nodes. This directory should be used for the installation of software packages. This means that the software package to be installed should be unpacked, compiled and linked in a subdirectory of $TMPDIR. The real installation of the package (e.g. make install) should be made into the $HOME folder.

Attention.svg
Note that you should not use /tmp or /scratch! Please use $TMPDIR instead.
The reason is that an automatic cleanup on /tmp or /scratch is not possible because another job could be still using data below these directories. Hence the corresponding file systems could fill up and this can cause issues for you and for other users. On the other hand, $TMPDIR is created when the job starts and removed when the job completes, i.e. a cleanup is automatically done.

Usage example for $TMPDIR
We will provide an example for using $TMPDIR and describe efficient data transfer to and from $TMPDIR.

If you have a data set with many files which is frequently used by batch jobs you should create a compressed archive on a workspace. This archive can be extracted on $TMPDIR inside your batch jobs. Such an archive can be read efficiently from a parallel file system since it is a single huge file. On a login node you can create such an archive with the following steps:

Create a workspace to store the archive
[ab1234@uc2n997 ~]$ ws_allocate data-ssd 60
Create the archive from a local dataset folder (example)
[ab1234@uc2n997 ~]$ tar -cvzf $(ws_find data-ssd)/dataset.tgz dataset/
Inside a batch job extract the archive on $TMPDIR, read input data from $TMPDIR, store results on $TMPDIR and save the results on a workspace:

!/bin/bash
 very simple example on how to use local $TMPDIR
SBATCH -N 1
SBATCH -t 24:00:00

 Extract compressed input dataset on local SSD
tar -C $TMPDIR/ -xvzf $(ws_find data-ssd)/dataset.tgz

 The application reads data from dataset on $TMPDIR and writes results to $TMPDIR
myapp -input $TMPDIR/dataset/myinput.csv -outputdir $TMPDIR/results

 Before job completes save results on a workspace
rsync -av $TMPDIR/results $(ws_find data-ssd)/results-${SLURM_JOB_ID}/
LSDF Online Storage
In some cases it is useful to have access to the LSDF Online Storage on the HPC-Clusters also. Therefore the LSDF Online Storage is mounted on the Login- and Datamover-Nodes. Furthermore it can be used on the compute nodes during the job runtime with the constraint flag "LSDF" (Slurm common features ). There is also an example about the LSDF batch usage: Slurm LSDF example .

 !/bin/bash
 SBATCH ...
 SBATCH --constraint=LSDF

For the usage of the LSDF Online Storage the following environment variables are available: $LSDF, $LSDFPROJECTS, $LSDFHOME. Please request storage projects in the LSDF Online Storage seperately: LSDF Storage Request.

BeeOND (BeeGFS On-Demand)
Users of the UniCluster have possibility to request a private BeeOND (on-demand BeeGFS) parallel filesystem for each job. The file system is created during job startup and purged after your job.

IMPORTANT:
All data on the private filesystem will be deleted after your job. Make sure you have copied your data back to the global filesystem (within job), e.g., $HOME or any workspace.
BeeOND/BeeGFS can be used like any other parallel file system. Tools like cp or rsync can be used to copy data in and out.

For detailed usage see here: Request on-demand file system

Backup and Archiving
There are regular backups of all data of the home directories,whereas ACLs and extended attributes will not be backuped.

Please open a ticket if you need backuped data.

JUSTUS2/Hardware
< JUSTUS2
(Redirected from Hardware and Architecture (bwForCluster JUSTUS 2))
Jump to navigationJump to search
The bwForCluster JUSTUS 2 is a state-wide high-performance compute resource dedicated to Computational Chemistry and Quantum Sciences in Baden-Württemberg, Germany.

Contents
1 System Architecture
1.1 Operating System and Software
1.2 Common Hardware Features
1.3 Node Specifications
1.4 Storage Architecture
1.4.1 $HOME
1.4.2 Workspaces
1.4.3 $SCRATCH and $TMPDIR
1.5 Backup
System Architecture
The HPC cluster is composed of login nodes, compute nodes and parallel storage systems connected by fast data networks. It is connected to the Internet via Baden Württemberg's extended LAN BelWü (light blue).

Overview on JUSTUS 2 hardware architecture. All nodes are additionally connected by 1GB Ethernet.
Users log in on one of the four login nodes and have access to their home and working directories (darker blue) stored in the parallel file system Lustre.

Two additional special login visualization node enable users to visualize compute results directly on the cluster.

Calculations are done on the several types of compute nodes (top), which are accessed via the batch queuing system Slurm .

Operating System and Software
Operating System: Rocky Linux 8
Queuing System: Slurm (also see: Slurm HOWTO (JUSTUS 2))
Environment Modules for site specific scientific applications, developer tools and libraries
Common Hardware Features
The system consists of 702 nodes (692 compute nodes and 10 dedicated login, service and visualization nodes) with 2 processors each and a total of 33,696 processor cores.

Processor: 2 x Intel Xeon 6252 Gold (Cascade Lake, 24-core, 2.1 GHz)
Two processors per node (2 x 24 cores)
Omni-Path 100 Gbit/s interconnect
Node Specifications
As a short overview of the table below: There are different types of compute node:

500 "standard" nodes (44 upgraded to "medium" nodes with more RAM later)
168 SSD nodes: additional RAM and fast SSD disks
8 large nodes: larger disks and even more RAM
14 nodes with GPGPU accelerators
Common to all nodes of the cluster are the following properties:

Two CPU Chips (Sockets): 2 x Intel Xeon E6252 Gold (Cascade Lake)
24 compute core per CPU, so 48 core per node
Interconnect: Omni-Path 100
The nodes are tiered in terms of hardware configuration (amount of memory, local NVMe, hardware accelerators) in order to be able to serve a large range of different job requirements flexibly and efficiently.

Node Type Quantity Cores Memory Local NVMe SSD Accelerator
Standard Nodes 456 48 192 GB --- ---
Medium Nodes 44 48 384 GB --- ---
SSD Nodes 148 48 384 GB 2 x 1.6 TB (RAID 0) ---
Medium SSD Nodes 20 48 768 GB 2 x 1.6 TB (RAID 0) ---
Large SSD Nodes 8 48 1536 GB 5 x 1.6 TB (RAID 0) ---
Special Nodes 14 48 192 GB --- 2 x Nvidia V100S
Login- and Service Nodes 8 48 192 GB 2 x 2.0 TB (RAID 1) ---
Visualization Nodes 2 48 192 GB 2 x 2.0 TB (RAID 1) Nvidia Quadro P4000 Graphics

Core numbers: hyperthreading is enabled, so 48 core-nodes appear to have 96 cores.

Storage Architecture
The bwForCluster JUSTUS 2 provides of two independent distributed parallel file systems, one for the user's home directories $HOME and another one for global workspaces. This storage architecture is based on Lustre and can be accessed in parallel from any nodes. Additionally, some compute nodes (fast I/O nodes) provide locally attached NVMe storage devices for I/O demanding applications.

$HOME Workspace $SCRATCH $TMPDIR
Visibility global global node local node local
Lifetime permanent workspace lifetime (max. 90 days, extension possible) batch job walltime batch job walltime
Total Capacity 250 TB 1200 TB 3000 GB / 7300 GB per node max. half of RAM per node
Disk Quotas 400 GB per user 20 TB per user none none
File Quotas 2.000.000 files per user 5.000.000 files per user none none
Backup yes no no no
 global             : accessible from all nodes
 local              : accessible from allocated node only
 permanent          : files are stored permanently (as long as user can access the system)
 batch job walltime : files are removed at end of the batch job
Note: Disk and file quota limits are soft limits and are subject to change. Quotas feature a grace period where users may exceed their limits to some extent (currently 20%) for a brief period of time (currently 4 weeks).

$HOME
Home directories are meant for permanent file storage of files that are keep being used like source codes, configuration files, executable programs etc.; the content of home directories will be backed up on a regular basis.

Current disk usage on home directory and quota status can be checked with the command lfs quota -h -u $USER /lustre/home.

Note: Compute jobs on nodes must not write temporary data to $HOME. Instead they should use the local $SCRATCH or $TMPDIR directories for very I/O intensive jobs and workspaces for less I/O intensive jobs.

Workspaces
More info on our general page:

→ Workspaces

Workspaces can be generated through the workspace tools. This will generate a directory with a limited lifetime on the parallel global work file system. When this lifetime is reached the workspace will be deleted automatically after a grace period. Users will be notified by daily e-mail reminders starting 7 days before expiration of a workspace. Workspaces can (and must) be extended to prevent deletion at the expiration date.

Defaults and maximum values

Default lifetime (days) 7
Maximum lifetime 90
Maximum extensions unlimited
Examples

Command Action
ws_allocate my_workspace 30 Allocate a workspace named "my_workspace" for 30 days.
ws_list List all your workspaces.
ws_find my_workspace Get absolute path of workspace "my_workspace".
ws_extend my_workspace 30 Set expiration date of workspace "my_workspace" to 30 days (regardless of remaining days).
ws_release my_workspace Manually erase your workspace "my_workspace" and release used space on storage (remove data first for immediate deletion of the data).
Current disk usage on workspace file system and quota status can be checked with the command lfs quota -h -u $USER /lustre/work.

Note: The parallel work file system works optimal for medium to large file sizes and non-random access patterns. Large quantities of small files significantly decrease IO performance and must be avoided. Consider using local scratch for these.

$SCRATCH and $TMPDIR
On compute nodes the environment variables $SCRATCH and $TMPDIR always point to local scratch space that is not shared across nodes.

$TMPDIR always points to a directory on a local RAM disk which will provide up to 50% of the total RAM capacity of the node. Thus, data written to $TMPDIR will always count against allocated memory.

$SCRATCH will point to a directory on locally attached NVMe devices if (and only if) local scratch has been explicitly requested at job submission (i.e. with --gres=scratch:nnn option). If no local scratch has been requested at job submission $SCRATCH will point to the very same directory as $TMPDIR (i.e. to the RAM disk).

On the login nodes $TMPDIR and $SCRATCH point to a local scratch directory on that node. This is located at /scratch/<username> and is also not shared across nodes. The data stored in there is private but will be deleted automatically if not accessed for 7 consecutive days. Like any other local scratch space, the data stored in there is NOT included in any backup.

Backup
Only files in your $HOME directory are included in a backup and can be restored in case of accidental deletion. The files in the "Work" filesystem are not intended for permanent storage during your jobs. Sort your results well and save important data in $HOME.

#### BwForCluster MLS&WISO Production Hardware

Jump to navigationJump to search
There is currently no text in this page. You can search for this page title in other pages, or search the related logs, but you do not have permission to create this page.

#### BwForCluster MLS&WISO Development Hardware

Jump to navigationJump to search
There is currently no text in this page. You can search for this page title in other pages, or search the related logs, but you do not have permission to create this page.

#### BwForCluster NEMO Hardware and Architecture

Jump to navigationJump to search
There is currently no text in this page. You can search for this page title in other pages, or search the related logs, but you do not have permission to create this page.

#### BinAC/Hardware and Architecture

< BinAC
(Redirected from BwForCluster BinAC Hardware and Architecture)
Jump to navigationJump to search

Contents
1 System Architecture
1.1 Operating System and Software
1.2 Compute Nodes
1.3 Special Purpose Nodes
2 Storage Architecture
2.1 $HOME
2.2 Work Space
2.3 Local Disk Space
2.4 SDS@hd
System Architecture
The bwForCluster BinAC is intended for compute activities related to Bioinformatics and Astrophysics research.

Operating System and Software
Operating System: RHEL 7
Queuing System: MOAB / Torque (see Batch Jobs for help)
(Scientific) Libraries and Software: Environment Modules

Compute Nodes
BinAC offers 236 compute nodes, 62 GPU nodes plus several special purpose nodes for login, interactive jobs, etc.

Compute node specification:

Standard Fat GPU
Quantity 236 4 62
Processors 2 x Intel Xeon E5-2630v4 (Broadwell) 4 x Intel Xeon E5-4620v3 (Haswell) 2 x Intel Xeon E5-2630v4 (Broadwell)
Processor Frequency (GHz) 2.4 2.0 2.4
Number of Cores 28 40 28
Working Memory (GB) 128 1024 128
Local Disk (GB) 256 (SSD) 256 (SSD) 256 (SSD)
Interconnect FDR FDR FDR
Coprocessors – – 2 x Nvidia Tesla K80
Special Purpose Nodes
Besides the classical compute node several nodes serve as login and preprocessing nodes, nodes for interactive jobs and nodes for creating virtual environments providing a virtual service environment.

Storage Architecture
The bwForCluster BinAC consists of two separate storage systems, one for the user's home directory $HOME and one serving as a work space. The home directory is limited in space and parallel access but offers snapshots of your files and Backup. The work space is a parallel file system which offers fast and parallel file access and a bigger capacity than the home directory. This storage is based on BeeGFS and can be accessed parallel from many nodes. Additionally, each compute node provides high-speed temporary storage (SSD) on the node-local solid state disk via the $TMPDIR environment variable.

$HOME Work Space $TMPDIR
Visibility global global node local
Lifetime permanent work space lifetime (max. 30 days, max. 3 extensions) batch job walltime
Capacity unkn. 482 TB 211 GB per node
Quotas 40 GB per user none none
Backup yes no no
 global             : all nodes access the same file system
 local              : each node has its own file system
 permanent          : files are stored permanently
 batch job walltime : files are removed at end of the batch job

$HOME
Home directories are meant for permanent file storage of files that are keep being used like source codes, configuration files, executable programs etc.; the content of home directories will be backed up on a regular basis.

 NOTE:
 Compute jobs on nodes must not write temporary data to $HOME.
 Instead they should use the local $TMPDIR directory for I/O-heavy use cases
 and work spaces for less I/O intense multinode-jobs.

Work Space
Work spaces can be generated through the workspace tools. This will generate a directory on the parallel storage.

To create a work space you'll need to supply a name for your work space area and a lifetime in days. For more information read the corresponding help, e.g: ws_allocate -h.

Examples:

Command Action
ws_allocate mywork 30 Allocate a work space named "mywork" for 30 days.
ws_allocate myotherwork Allocate a work space named "myotherwork" with maximum lifetime.
ws_list -a List all your work spaces.
ws_find mywork Get absolute path of work space "mywork".
ws_extend mywork 30 Extend life me of work space mywork by 30 days from now. (Not needed, workspaces on BinAC are not limited).
ws_release mywork Manually erase your work space "mywork". Please remove directory content first.
Local Disk Space
All compute nodes are equipped with a local SSD with 200 GB capacity for job execution. During computation the environment variable $TMPDIR points to this local disk space. The data will become unavailable as soon as the job has finished.

SDS@hd
SDS@hd is mounted only on login03 at /sds_hd. To access your Speichervorhaben, please see the SDS@hd documentation. If you can't see your Speichervorhaben, you can open a ticket.

#### Hardware Overview¶

HoreKa is a distributed memory parallel computer consisting of hundreds of individual servers called "nodes". Each node has two Intel Xeon processors, at least 256 GB of local memory, local NVMe SSD disks and two high-performance network adapters. All nodes are connected by an extremely fast, low-latency InfiniBand 4X HDR interconnect. In addition two large parallel file systems are connected to HoreKa.

The operating system installed on every node is Red Hat Enterprise Linux (RHEL) 9.x. On top of this operating system, a set of (open source) software components like Slurm has been installed. Some of these components are of special interest to end users and are briefly discussed here. Others are mostly just of importance to system administrators and are thus not covered by this documentation.

The different server systems in HoreKa have different roles and offer different services.

horeka-cpu.jpg
One of the CPUs used by HoreKa (Simon Raffeiner, KIT/SCC)
Login Nodes

The login nodes are the only nodes directly accessible to end users. These nodes can be used for interactive logins, file management, software development and interactive pre- and postprocessing. Four nodes are dedicated as login nodes.

Compute Nodes

The vast majority of the nodes is dedicated to computations. These nodes are not directly accessible to users, instead the calculations have to be submitted to a so-called batch system. The batch system manages all compute nodes and executes the queued jobs depending on their priority and as soon as the required resources become available. A single job may use hundreds of compute nodes and many thousand CPU cores at once.

Data Mover Nodes

Two nodes are reserved for data transfers between the different HPC file systems and other storage systems.

Administrative Service Nodes

Some nodes provide additional services like resource management, external network connections, monitoring, security etc. These nodes can only be accessed by system administrators.

HoreKa compute node hardware¶
HoreKa consists of different partitions, accelerated ones or without accelerators.

HoreKa Blue nodes provide CPU-only compute power. There are nodes types with different amount of main memory. In operation since 06/2021 and 02/23 (Extra-Large-Memory).
HoreKa Green nodes feature 4x NVIDIA A100 GPUs. In operation since 06/2021.
HoreKa Teal nodes are equipped with 4x NVIDIA H100 GPUs. In operation since 05/2024. One node is equipped with 8x NVIDIA H200 GPUs, in operation since 10/2025.
HoreKa Ruby nodes are equipped with 4x NVIDIA H200 GPUs. In operation since 08/2025.
Node Type HoreKa Blue
Standard /
High-Memory /
Extra-Large-Memory nodes HoreKa Green
Accelerated
4x A100 HoreKa Teal
Accelerated
4x H100 HoreKa Teal
Accelerated
8x H200 HoreKa Ruby
Accelerated
4x H200
No. of nodes 570 / 32 / 8 167 22 1 13
CPUs Intel Xeon Platinum 8368 Intel Xeon Platinum 8368 AMD EPYC 9354 Intel Xeon Platinum 8568Y+ AMD EPYC 9454
CPU Sockets per node 2 2 2 2 2
CPU Cores / Threads per node 76 / 152 76 / 152 64 / 128 96 / 192 96 / 192
Main memory 256 / 512 / 4096 GiB 512 GiB 768 GiB 2048 GiB 768 GiB
Accelerators - 4x NVIDIA A100-40 4x NVIDIA H100-94 8x NVIDIA HGX H200 4x NVIDIA HGX H200
Memory per accelerator - 40 GB 94 GB 141 GB 141 GB
Local disks 960 GB NVMe SSD /
960 GB NVMe SSD /
7 x 3,84 TB NVMe SSD 960 GB NVMe SSD 2 x 3,84 TB NVMe SSD 8 x 3,84 TB NVMe SSD 15,36 TB NVMe SSD
Interconnect InfiniBand HDR InfiniBand HDR 4x NDR200 8x NDR400 4x NDR400
Interconnect¶
An important component of HoreKa is the InfiniBand 4X HDR 200 GBit/s interconnect. All nodes are attached to this high-throughput, very low-latency (~ 1 microsecond) network. InfiniBand is ideal for communication intensive applications and applications that e.g. perform a lot of collective MPI communications.

A look at some of the InfiniBand ports in the HoreKa interconnect (Simon Raffeiner, KIT/SCC)

Multicore processors
During the last century, processors got faster due to progressing miniaturisation: Shrinking sizes of components allowed higher transistor densities and higher CPU frequencies (Moore's Law). This trend stopped around 2004 when the miniaturisation hit its physical and technical limits. Nowadays, running processors in parallel is the only reasonable way to increase the performance.

Das Bild zeigt ein vereinfachtes Diagramm einer Mehrkern-CPU.

Struktur:

- **Chip** (äußere Umrandung)
- Darin vier CPU-Kerne: **C1**, **C2**, **C3**, **C4**
- Unter jedem Kern befinden sich zwei Cache-Stufen: **L1** und darunter **L2**
- Darunter ein gemeinsamer **L3-Cache**, der von allen Kernen genutzt wird
- Der L3-Cache ist über eine **Memory Interface**-Einheit mit dem **Main Memory** verbunden
- Rechts vom Memory Interface befindet sich ein Anschluss zu **Peripherals** (z. B. I/O-Geräte)

Das Diagramm zeigt das typische Layout einer modernen Multi-Core-CPU mit mehreren Cache-Hierarchien und einer gemeinsamen Speicheranbindung.

Figure 1: Scheme of a quad-core processor.
Figure 1 shows the scheme of a multicore processor with four independent processors called cores (C1 to C4). The memory interface connects the cores to the peripherals (network interface, disks, ...) and to the common, shared main memory. All cores have access to the same data stored in main memory.

As data transfer between main memory and the cores is relatively slow, fast, but small data buffers are integrated on the chip. These buffers are called caches and are usually arranged in a hierarchy of three levels L1, L2 and L3 as shown in Figure 1.

Das Bild zeigt zwei miteinander verbundene Mehrkern-CPUs, also ein typisches NUMA-System (Non-Uniform Memory Access).

Für jede CPU:

- Vier Kerne: **C1**, **C2**, **C3**, **C4**
- Unter jedem Kern: **L1**- und **L2**-Cache
- Gemeinsamer **L3**-Cache pro CPU
- Ein **Memory Interface**, das den L3-Cache mit dem **Main Memory** dieser CPU verbindet

Beide CPUs:

- Haben jeweils eigenen Hauptspeicher (zwei getrennte „Main Memory“-Blöcke)
- Sind über eine Verbindung zwischen den beiden Memory Interfaces gekoppelt
- Teilen sich eine gemeinsame Peripherieanbindung („Peripherals“)

Das Diagramm zeigt also ein Dual-Socket-System:  
Jede CPU hat ihren eigenen Speicher, kann aber über die Interconnect-Verbindung auch auf den Speicher der anderen CPU zugreifen.

Figure 2: Scheme of a dual-socket node with eight cores.
Due to technical limitations, it is not possible to integrate more than around 16 cores on a multicore processor chip. Instead, two multicore processors are coupled as shown in Figure 2. Each core has access to both main memories: The shared memory consists of the main memories of both multicore processors. This is called a dual-socket node.

If several cores perform read and write operations on the same data, the cache administration has to guarantee that each core sees the actual values of the data. It is difficult to ensure this consistency between caches and memory for shared memory systems with more than about 30 cores. The only way out is connecting some dual-socket nodes by a fast data network as shown in Figure 3.

Das Bild zeigt vier Multi-Core-CPUs (jeweils mit mehreren Kernen und Cache-Hierarchie), die alle an einem gemeinsamen Interconnect angebunden sind.

Struktur:

- Jede CPU besitzt:
  - Mehrere Kerne mit L1- und L2-Cache
  - Einen gemeinsamen L3-Cache
  - Eine Memory-Interface-Einheit
  - Ein eigenes Main-Memory-Modul darunter

- Die vier CPUs sind vertikal nach unten an eine gemeinsame, grüne Verbindungslinie angebunden.

Die grüne Linie symbolisiert ein Cluster-Interconnect oder Hochgeschwindigkeitsnetzwerk, das mehrere NUMA-Nodes bzw. ganze Rechnerknoten verbindet.

Das Diagramm stellt also mehrere unabhängige Rechenknoten dar, die über ein gemeinsames Netzwerk (z. B. InfiniBand) gekoppelt sind.
Das Bild zeigt vier Multi-Core-CPUs (jeweils mit mehreren Kernen und Cache-Hierarchie), die alle an einem gemeinsamen Interconnect angebunden sind.

Struktur:

- Jede CPU besitzt:
  - Mehrere Kerne mit L1- und L2-Cache
  - Einen gemeinsamen L3-Cache
  - Eine Memory-Interface-Einheit
  - Ein eigenes Main-Memory-Modul darunter

- Die vier CPUs sind vertikal nach unten an eine gemeinsame, grüne Verbindungslinie angebunden.

Die grüne Linie symbolisiert ein Cluster-Interconnect oder Hochgeschwindigkeitsnetzwerk, das mehrere NUMA-Nodes bzw. ganze Rechnerknoten verbindet.

Das Diagramm stellt also mehrere unabhängige Rechenknoten dar, die über ein gemeinsames Netzwerk (z. B. InfiniBand) gekoppelt sind.

Figure 3: Two dual-socket nodes connected to a fast data network (green line).

## 11 File Systems and Access Control

### Overview

"Rule of thumb"
On the bwHPC clusters, you have access to three different file systems:
your home directory $HOME
one or more working directories (workspaces)
a temporary directory $TMP or similar

1. Your home directory $HOME is a small, permanent directory for source code, configuration files, executable programs and scripts. Usually, it is backed up.

Safety instructions

Hidden files and directories inside $HOME (those starting with a dot: ".*") should not be writable by others, not even for the group. These files are often automatically read in or are automatically executed, e.g. .profile.

See the page Access Rights and Access Control for more information.

2. There are large, global, temporary working directories, well suited for large amounts of input and output data. "Global" means that your working directories are accessible from all compute nodes. "Temporary" means that the lifetime is limited to some hundred days and that old files might be deleted automatically. Working directories are usually NOT backed up.

The working directories are called workspaces and have to be allocated by the user.

3. There might be local, non-global, temporary storage on the computing nodes usually named $TMP, $TMPDIR or something similar. The data stored there will be wiped when the compute job ends.

### Your $HOME Directory

After having logged in, you are in your home directory.

Example: Try

Das Terminal zeigt folgende Schritte:

`ls`  
→ Ausgabe: `test`

`cd test`

`pwd`  
→ `/home/st/st_us-403340/st_ac117776/test`

`echo $HOME`  
→ `/home/st/st_us-403340/st_ac117776`

`cd $HOME`

`ls`  
→ `test`

`pwd`  
→ `/home/st/st_us-403340/st_ac117776`

Der Nutzer hat erfolgreich zwischen dem Verzeichnis *test* und seinem Home-Verzeichnis gewechselt. Das Home-Verzeichnis enthält die Datei bzw. das Verzeichnis *test*.

Example: Using the environment variable $HOME.
Do not submit a job in your $HOME directory! Use a workspace instead! Your $HOME directory is intended only for small amounts of data like source code files, executable programs or scripts.

The disk space in your home directory is limited. On the bwUniCluster 2.0, the following command returns your current disk usage and your quota restrictions:
lfs quota -u $(whoami) $HOME

### Workspaces

On each cluster, you can manually allocate disk space on the parallel file system.

On bwUniCluster 2.0, you can allocate your workspace for at most 60 days and extend it three times, each extension is for at most 60 days. Altogether, the maximum lifetime of a workspaces is 240 days on bwUniCluster 2.0 and 90 days on JUSTUS 2.

The most important commands are listed in the following table:

| Befehl                     | Beschreibung                                                   |
|----------------------------|----------------------------------------------------------------|
| `$ ws_allocate myws 10`    | Allocate a workspace named „myws“ for 10 days.                 |
| `$ ws_list -a`             | List all your workspaces.                                      |
| `$ ws_find myws`           | Get absolute path of your workspace „myws“.                    |
| `$ ws_extend myws 5`       | Extend lifetime of workspace „myws“ by 5 days. You can extend 3 times. |
| `$ ws_release myws`        | Manually release your workspace myws.                          |

The commands show how to allocate, find, extend and release a workspace.
You can send yourself a calender entry reminding you of your workspace's expiration date:
$ ws_send_ical.sh < workspace > < email >

In the following example a workspace named "myws" is allocated for 60 days, and its path is stored in the environment variable WSDIR.

Das Terminal zeigt die Nutzung eines Workspace auf dem Cluster:

`ws_allocate myws 60`  
→ Workspace wird erstellt, Dauer: 1440 Stunden  
→ Weitere Verlängerungen verfügbar: 3  
→ Pfad: `/pfs/work7/workspace/scratch/st_ac117776-myws-0`

`ws_find myws`  
→ Gibt denselben Workspace-Pfad aus

`WSDIR=$(ws_find myws)`  
→ Speichert den Pfad in der Variable `WSDIR`

`echo $WSDIR`  
→ `/pfs/work7/workspace/scratch/st_ac117776-myws-0`

`cd $WSDIR`

`pwd`  
→ `/pfs/work7/workspace/scratch/st_ac117776-myws-0`

Der Nutzer befindet sich jetzt im eigenen Workspace-Verzeichnis.

How to allocate a workspace named "myws".
Before the end of the lifetime of your workspace, you have to allocate a new one if you want to keep your data. Please do not copy your data from the old workspace to the new one, but move it using the Linux command mv!

In the following video, Saskia Lück (Universität Mannheim) explains what workspaces are and how they are created, listed, extended  and deleted.

Video Player

00:00
03:01

"Workspace tools on bwHPC". Video by Saskia Lück.
Workspace
Jump to navigationJump to search
Workspace tools provide temporary scratch space so called workspaces for your calculation on a central file storage. They are meant to keep data for a limited time – but usually longer than the time of a single job run.

Contents
1 No Backup
2 Create workspace
3 List all your workspaces
4 Find workspace location
5 Extend lifetime of your workspace
6 Setting Permissions for Sharing Files
6.1 Workspace Tools
6.2 Regular Unix Permissions
6.3 ACLs: Access Control Lists
7 Delete a Workspace
8 Restore an Expired Workspace
No Backup
Workspaces are not meant for permanent storage, hence data in workspaces is not backed up and may be lost in case of problems on the storage system. Please copy/move important results to $HOME or storage space outside the cluster.

Create workspace
To create a workspace you need to state name of your workspace and lifetime in days. A maximum value for lifetime and a maximum number of renewals is defined on each cluster. Execution of:

  $ ws_allocate mySpace 30
e.g. returns:

  Workspace created. Duration is 720 hours.
  Further extensions available: 3
  /work/workspace/scratch/username-mySpace-0
For more information read the program's help, i.e. $ ws_allocate -h.

List all your workspaces
To list all your workspaces, execute:

  $ ws_list
which will return:

Workspace ID
Workspace location
available extensions
creation date and remaining time
To list expired workspaces, see Restore an Expired Workspace.

Find workspace location
Workspace location/path can be prompted for any workspace ID using ws_find, in case of workspace mySpace:

  $ ws_find mySpace
returns the one-liner:

  /work/workspace/scratch/username-mySpace-0

Extend lifetime of your workspace
Any workspace's lifetime can be only extended a cluster-specific number of times. There several commands to extend workspace lifetime

$ ws_extend mySpace 40
which extends workspace ID mySpace by 40 days from now,
$ ws_extend mySpace
which extends workspace ID mySpace by the number days used previously
$ ws_allocate -x mySpace 40
which extends workspace ID mySpace by 40 days from now.

Setting Permissions for Sharing Files
The examples will assume you want to change the directory in $DIR. If you want to share a workspace, DIR could be set with DIR=$(ws_find my_workspace)

Workspace Tools
ws_share
ws_share share workspacename username

allows you to grant the user username read access to the workspace.

Newer versions of the workspace tools have sharing options to ws_allocate:

-G option of ws_allocate
ws_allocate -G groupname workspacename duration

groupname: name of the group you want to share with
workspacename: what you want to call your workspace
duration: how long the workspace is supposed to last in days
Essentially this tool sets regular unix rwx permissions for the group plus the "suid" bit on the directory to make the permission inheritable.

Regular Unix Permissions
Making workspaces world readable/writable using standard unix access rights with chmod is only feasible if you are in a research group and you and your co-workers share a common ("bwXXXXX") unix group.

Do not make files readable or even writable to everyone or to large common groups ("all students").

Command Action
chgrp -R bw16e001 "$DIR"
chmod -R g+rX "$DIR"

Set group ownership and grant read access to group for files in workspace via unix rights to the group "bw16e001" (has to be re-done if files are added)
chgrp -R bw16e001 "$DIR"
chmod -R g+rswX "$DIR"

Set group ownership and grant read/write access to group for files in workspace via unix rights (has to be re-done if files are added). Group will be inherited by new files, but rights for the group will have to be re-set with chmod for every new file
Options used:

-R: recursive
g+rwx
g: group

- add permissions (- to remove)
rwx: read, write, execute
ACLs: Access Control Lists
ACLs allow a much more detailed distribution of permissions but are a bit more complicated and not visible in detail via "ls". They have the additional advantage that you can set a "default" ACL for a directory, (with a -d flag or a d: prefix) which will cause all newly created files to inherit the ACLs from the directory. Regular unix permissions only have limited support (only group ownership, not access rights) for this via the suid bit.

Best practices with respect to ACL usage:

Take into account that ACLs take precedence over standard unix access rights
The owner of a workspace is responsible for its content and management
Please note that ls (List directory contents) shows ACLs on directories and files only when run as ls -l as in long format, as "plus" sign after the standard unix access rights.

Examples with regard to "my_workspace":

Command Action
getfacl "$DIR" List access rights on $DIR
setfacl -Rm user:fr_xy1:rX,default:user:fr_xy1:rX "$DIR" Grant user "fr_xy1" read-only access to $DIR
setfacl -R -m user:fr_me0000:rwX,default:user:fr_me0000:rwX "$DIR"
setfacl -R -m user:fr_xy1:rwX,default:user:fr_xy1:rwX "$DIR"

Grant your own user "fr_me0000" and "fr_xy1" inheritable ("default") read and write access to $DIR, so you can also read/write files put into the workspace by a coworker
setfacl -Rm group:bw16e001:rX,default:group:bw16e001:rX "$DIR" Grant group (Rechenvorhaben) "bw16e001" read-only access to $DIR
setfacl -Rb "$DIR" Remove all ACL rights. Standard Unix access rights apply again.
Options used:

-R: recursive
-m: modify
user:username:rwX user: next name is a user; rwX read, write, eXecute (only where execute is set for user)
default:[user|group] set the default for user or group for new files or dierctories
Delete a Workspace
  $ ws_release mySpace # Manually erase your workspace mySpace
Note: workspaces are kept for some time after release. To immediately delete and free space e.g. for quota reasons, delete the files with rm before release.

Newer versions of workspace tools have a --delete-data flag that immediately deletes data. Note that deleted data from workspaces is permanently lost.

Restore an Expired Workspace
For a certain (system-specific) grace time following workspace expiration, a workspace can be restored by performing the following steps:

(1) Display restorable workspaces.

ws_restore -l
(2) Create a new workspace as the target for the restore:

ws_allocate restored 60
(3) Restore:

ws_restore <full_name_of_expired_workspace> restored
The expired workspace has to be specified using the full name, including username prefix and timestamp suffix (otherwise, it cannot be uniquely identified). The target workspace, on the other hand, must be given with just its short name as listed by ws_list, without the username prefix.

If the workspace is no visible/restorable, it has been permanently deleted and cannot be restored, not even by us. Please always remember, that workspaces are intended solely for temporary work data, and there is no backup of data in the workspaces.

### Access Rights and Access Control

In Linux, there are three different groups:
the owner (called user) of files and directories: user
the group the owner (user) belongs to: group
all the other users on the cluster: other
Each group can have three different rights concerning files and directories:
reading files and directories: read
writing, changing and deleting files and directories: write
executing files and changing to directories: execute
You can check these rights with the command ls -l.

Example:

How to check the access rights.
This means that the owner (st_ac117776) has all rights in the subdirectory test and can read and change the file testfile, while the members of the group st_us-403340 and all other users have access to the subdirectory test (and can read the files there) and can also read the file testfile.

It is highly recommended to restrict the access for the group and for others. Especially, nobody besides the owner should have access to sensitive data.

The access rights are changed with the command chmod.

Example:
Das Terminal zeigt Datei- und Verzeichnisrechte sowie deren Änderung:

`ls -l`  
→ zeigt:

- `test` (Verzeichnis) mit Rechten: `drwxr-xr-x`
- `testfile` (Datei) mit Rechten: `-rw-r--r--`

`chmod go-rx test`  
→ entfernt für Gruppe und andere (g/o) die Rechte r und x am Verzeichnis `test`

`chmod go-r testfile`  
→ entfernt für Gruppe und andere (g/o) das Leserecht an der Datei `testfile`

`ls -l`  
→ neue Rechte:

- `test`: `drwx------`  
- `testfile`: `-rw-------`

Der Benutzer hat die Verzeichnis- und Dateirechte erfolgreich eingeschränkt, sodass nur der Besitzer (st_ac117776) Zugriff besitzt.

How to restrict the access using chmod.
Some sensitive data is contained in hidden files in your home directory. You can list them with the command ls -al.

Example:
Die Ausgabe listet alle Dateien im Home-Verzeichnis, die mit `.bash` beginnen:

`ls -al .bash*`

Ergebnis:

- `.bash_history` — Größe 2962, geändert am Sep 1  
- `.bash_logout` — Größe 18, geändert am 22. Dez 2015  
- `.bash_profile` — Größe 176, geändert am 22. Dez 2015  
- `.bashrc` — Größe 124, geändert am 22. Dez 2015

Alle Dateien gehören dem Benutzer **st_ac117776** und haben die Rechte `-rw-------` (nur der Benutzer kann lesen und schreiben).

How to check the access rights of hidden files and subdirectories.
If you want to share data with your colleagues, you should store the data in workspaces and use ACLs to control the access.

Safety instructions

$HOME must not be writable by others, not even by the group. Otherwise someone else can delete or create files (even such like
.profile, .login etc. which are executed automatically) and delete, manipulate or create directories.

Files and directories that contain credentials (the .ssh directory, .vnc*, .git*, .*.conf etc.) must neither be writable nor readable for others, not even for the group. Otherwise someone else may be able to e.g. enter ssh keys, store another password hash for vnc
store and similar.

Even logfiles like .bash_history should not be readable for the group or others because they may contain passwords if you type passwords at the wrong time or in the wrong window.

Access rights should be checked occasionally, e.g. after transfer to another system. Especially when transferring data from Windows to Linux, permissions can be lost or changed.

## 12 The Software System: Modulefiles

### Introduction: What Are Modulefiles?

On a compute cluster, numerous software packages, libraries and compilers are installed, often in different versions. Each of these requires the setting of environment variables, e. g. the paths to the binaries and the man pages.

The manual setup is complicated and error-prone. Therefore, the necessary pieces of information and instructions are stored in modulefiles which are loaded by the user when needed.

In the following screencast, Karsten Siegmund (University of Ulm) explains the environment module system.

### Available Modulefiles

Available modulefiles are the modulefiles that can be loaded by the user. They may depend on the already loaded modules.

If you want to list all modulefiles, you must use the command
$ module spider

In order to get an overview over the available modulefiles, use the command
$ module avail
It displays the modulefiles on the screen, for example:
Die Ausgabe zeigt verfügbare Module auf dem Cluster mittels:

`module avail`

Die Module sind gruppiert unter:  
`/opt/bwhpc/common/modulefiles/Core`

Beispiele der aufgelisteten Module:

**bio:**

- bio/freesurfer/6.0.0
- bio/fsl/6.0.4
- bio/nest/2.18.0 (T)
- bio/nest/2.20.1 (T,D)

**cae:**

- cae/cgns/3.4.1-intel-19.1
- cae/cgns/4.1.2-gnu-8.3 (D)
- cae/openfoam/v2006-impi
- cae/openfoam/v2012
- cae/openfoam/v2106-impi
- cae/openfoam/4.1-extend
- cae/openfoam/5.x
- cae/openfoam/7
- cae/openfoam/8
- cae/openfoam/9 (D)
- cae/paraview/5.8
- cae/paraview/5.9

**devel:**

- devel/scorep/7.0-intel-19.1-openmpi-4.1
- devel/swig/4.0.2
- devel/tbb/2021.3.0
- devel/valgrind/3.16.1
- devel/vampir/9.9
- devel/vampir/9.10 (D)
- devel/vtune/2021.5.0

**jupyter:**

- jupyter/base/2021-08-03
- jupyter/base/2021-09-30
- jupyter/tensorflow/2021-08-03 (D)
- jupyter/tensorflow/2021-09-30 (D)

**lib:**

- lib/CGAL/5.3
- lib/hdf5/1.12.0-pgi-2020-openmpi-4.0
- lib/hdf5/1.12.0-gnu-8.3
- lib/hdf5/1.12.0-gnu-10.2-openmpi-4.0
- lib/hdf5/1.12.0-intel-19.1-openmpi-4.0
- lib/hdf5/1.10.5 (D)
- lib/netcdf/4.7.3-intel-19.1 (D)
- lib/netcdf/4.7.4-gnu-8.3 (D)

**math:**

- math/R/3.6.3 (D)

Kennzeichnungen:

- **(T)**: Modul ist derzeit geladen („T“ für *Taken* oder *Currently Loaded*)
- **(D)**: Default-Version eines Moduls

Die Liste zeigt die für Benutzer verfügbaren Softwaremodule des HPC-Clusters.

Part of the output of the command "module avail".
If you are interested only in the modulefiles belonging to, for example, the category "compiler", use the command
$ module avail compiler
in order to display only the modulefiles beginning with "compiler":

Die Ausgabe von:

`module avail compiler`

zeigt verfügbare Compiler-Module unter  
`/opt/bwhpc/common/modulefiles/Core`.

**GNU-Compiler (gcc/g++):**

- compiler/gnu/8.3.1
- compiler/gnu/9.3
- compiler/gnu/10.2 (D)   ← Default
- compiler/gnu/10.3
- compiler/gnu/11.1

**Clang/LLVM:**

- compiler/clang/9.0
- compiler/llvm/10.0
- compiler/llvm/11.0
- compiler/llvm/12.0 (D)

**Intel-Compiler:**

- compiler/intel/18.0
- compiler/intel/19.0
- compiler/intel/19.1
- compiler/intel/2021.3.0
- compiler/intel/2021.3.0_llvm (D)

**PGI/NVIDIA HPC SDK:**

- compiler/pgi/2020
- toolkit/nvidia-hpc-sdk/21.2-byo-compiler

**Intel oneAPI Compiler:**

- toolkit/oneAPI/compiler-rt/2021.1.1
- toolkit/oneAPI/compiler/2021.1.1

Legende:

- **(D)** = Default Module

Hinweise unten:

- „module spider“ zeigt alle Module und Erweiterungen.
- „module keyword <keys>“ sucht nach passenden Modulen.

Output of "module avail compiler".
Modulefiles are sorted by categories, software names and versions:
< category >/< software_name >/< version >.

| Kategorie   | Beschreibung                                                                            |
|-------------|------------------------------------------------------------------------------------------|
| **compiler/** | for compiler, e.g. intel, gnu, pgi, open64                                              |
| **devel/**    | for debugger, e.g. ddt, and development tools, e.g. cmake, itrac                        |
| **mpi/**      | for MPI libraries, e.g. impi, openmpi, mvapich(2)                                       |
| **numlib/**   | for numerical libraries, e.g. Intel MKL, ACML, nag, gsl, fftw                           |
| **lib/**      | for other libraries, e.g. netcdf, global array                                          |
| **bio/**      | for biology software, e.g. bowtie, abyss, mrbayes                                       |
| **cae/**      | for CAE software, e.g. ansys, abaqus, fluent                                            |
| **chem/**     | for chemistry software, e.g. gromacs, dacapo, turbomole                                 |
| **math/**     | for mathematics software, e.g. matlab, R                                                |
| **phys/**     | for physics software, e.g. geant4                                                       |
| **vis/**      | for visualisation software, e.g. vmd, tigervnc

This table shows most of the categories.
If you want to know how to use modulefiles in general, use the command
$ module help

The Cluster Information System CIS is a GUI version of the available and scheduled modules.

#### BwUniCluster2.0/Software

< BwUniCluster2.0
(Redirected from BwUniCluster 2.0 Software)
Jump to navigationJump to search

Contents
1 Environment Modules
2 Available Software
3 Software in Containers
4 Documentation
5 Documentation in the Wiki
Environment Modules
Most software is provided as Modules.

Required reading to use: Software Environment Modules

Available Software
Visit <https://www.bwhpc.de/software.php>, select Cluster → bwUniCluster 2.0

On cluster: module avail

Software in Containers
Instructions for loading software in containers: BwUniCluster2.0/Containers

Documentation
Documentation for environment modules is available on the cluster:

with command module help
examples in $SOFTNAME_EXA_DIR
Documentation in the Wiki
For some environment modules additional documentation is provided here.

Ansys
Mathematica
Matlab
Molden
OpenFoam
Python Dask
R
R/Glmnet
R/Rgdal
R/Rgdal (R 4.2.1)
R/Rjags
R/Rstan
R/cummeRbund
R/stringi
R/terra
R/terra (R 4.2.1)
Start vnc desktop
Turbomole

### How to Load and Unload Modulefiles?

The command
$ module load <category>/<software_name>/<version>
loads the modulefile for the software <software_name> of version <version>.

Omitting the version loads the default modulefile of this software:
$ module load <category>/<software_name>

Example: Intel compiler
The command
$ module load compiler/intel mpi/impi
loads two modulefiles: the default versions of the Intel compiler suite and of Intel-MPI (as at October 2021). This can be checked with the command
$ module list
which displays all loaded modules.

Die Ausgabe zeigt das Laden und Anzeigen von Modulen:

`module load compiler/intel mpi/impi`  
→ Lädt den Intel-Compiler sowie die Intel-MPI-Implementierung.

`module list`  
→ Ausgabe:

Currently Loaded Modules:  

1) compiler/intel/2021.3.0  
2) mpi/impi/2021.3.0

Beide Module wurden erfolgreich geladen.

Example: Intel compiler
The names of the modulefiles indicate implicit dependencies:
<category>/<software_name>/<version>-<attributes>-<dependencies>

Example:
Modulefile numlib/petsc/3.13.4-gnu-10.2-openmpi-4.0 means the PETSc version 3.13.4, compiled with the GNU Compiler Collection 10.2 and OpenMPI version 4.0.

If different software versions are loaded in the same session, the first one is unloaded automatically:

You can unload a loaded modulefile with name <module_name> by using the commands
$ module unload <module_name>
or
$ module remove <module_name>

Modulefiles change the shell session's environment variables and have to be loaded in batch job scripts, too.

### How to Get Information About a Modulefile?

In order to get help about a modulefile with name < module_name >, use the command
$ module help < module_name >

Example: The output of the command $ module help compiler/intel :

Die Ausgabe stammt von:

`module help compiler/intel`

Angezeigt wird die modul-spezifische Hilfe für **compiler/intel/2021.3.0**.

Inhalt:

Intel C/C++ and Fortran compiler Classic 2021.3.0  
Details unter:  
<https://software.intel.com/en-us/intel-compilers>

Bei Problemen Kontakt:  
Hartmut Häfner <hartmut.haefner@kit.edu>

SCC support end: 2022-12-31

Weiterführende Dokumentation:

- Intel C++ Compiler Classic Developer Guide and Reference  
  <https://software.intel.com/content/www/us/en/develop/documentation/cpp-compiler-developer-guide-and-reference>
- Intel Fortran Compiler Classic Developer Guide and Reference  
  <https://software.intel.com/content/www/us/en/develop/documentation/fortran-compiler-oneapi-dev-guide-and-reference/top.html>

Module specific help
The command
$ module whatis <module_name>
displays some short information about the module.

Example: The output of the command $ module whatis compiler/intel:

Die Ausgabe von:

`module whatis compiler/intel`

zeigt eine Kurzbeschreibung des Moduls:

compiler/intel/2021.3.0  
: Sets up Intel C/C++ and Fortran compiler Classic version (2021.3.0) – supported by SCC till 2022-12-31!

Output of "module whatis"
If you want to know the instructions of a modulefile with name <module_name>, use the command
$ module show <module_name>
The output shows which environment variables are set when the modulefile is loaded.

Example: The command$ module show compiler/intelshows:

Die Ausgabe von:

`module show compiler/intel`

zeigt den vollständigen Inhalt der Moduldatei  
`/opt/bwhpc/common/modulefiles/Core/compiler/intel/2021.3.0.lua`.

Wichtigste gesetzte Variablen:

- **INTEL_LICENSE_FILE**  
  `28518@scclic1.scc.kit.edu`

- Compiler-Binaries:  
  - **AR** → `xiar`  
  - **CC** → `icc`  
  - **CXX** → `icpc`  
  - **F77** → `ifort`  
  - **FC** → `ifort`

- Compiler-Flags (Optimierung + AVX2):  
  - **CFLAGS**: `-O2 -xCORE-AVX2`  
  - **CXXFLAGS**: `-O2 -xCORE-AVX2`  
  - **FFLAGS**: `-O2 -xCORE-AVX2`  
  - **FCFLAGS**: `-O2 -xCORE-AVX2`

- Pfade:  
  - **INTEL_VERSION** → `2021.3.0`  
  - **INTEL_HOME** → `/software/all/toolkit/Intel_OneAPI/compiler/2021.3.0/`  
  - **INTEL_BIN_DIR**  
  - **INTEL_INC_DIR**  
  - **INTEL_INCLUDE_DIR**  
  - **INTEL_LIB_DIR**  
  - **INTEL_MAN_DIR**  
  - **INTEL_DOC_DIR**

- **GDB_VERSION** → `10.1.2`

Die `module show`-Ausgabe enthüllt also exakt, welche Umgebungsvariablen gesetzt oder überschrieben werden, wenn das Intel-Compiler-Modul geladen wird.

Part of the output of "module show"

### Batch Systems: What do they do?

Let's have a look at a HPC cluster. It consists of some front ends (also called login nodes), a so-called head node and a lot of compute nodes:

Die Grafik zeigt das Prinzip eines HPC-Clusters und wie Nutzer ihre Jobs einreichen.

Links stehen drei Nutzer: **user1**, **user2**, **user3**.  
Jeder reicht Jobs ein (job1, job2, job3, job4).

Ablauf:

- Alle Jobs gehen zuerst an einen **Front End**-Knoten.
- Vom Front End gelangen sie an den **Head Node** des Clusters.
- Der Head Node entscheidet per Scheduler, welcher Job auf welchen Compute-Knoten laufen darf.

Im Clusterbereich:

- Mehrere farbige Kacheln stellen Rechenknoten dar.
- Einige Knoten sind frei („free“), andere laufen bereits Jobs.
- Beispiel:
  - job1 (grün) wird mehrfach auf verfügbaren Knoten platziert.
  - job2 (violett) belegt bestimmte Knoten.
  - job3 (orange) läuft auf wenigen Knoten.
  - job4 (türkis) wird auf freie Knoten verteilt.

Pfeile zeigen:

- **access granted** (Jobs dürfen laufen)
- **access blocked** (Job kann nicht starten, weil kein passender Knoten frei ist)

Zusammengefasst:  
Die Grafik verdeutlicht, dass Jobs nie direkt auf Rechenknoten gestartet werden, sondern über Front End und Head Node in die Warteschlange gelangen. Der Scheduler verteilt die Jobs anschließend automatisch auf die verfügbaren Ressourcen.

Figure 1: Functionality of a batch system.
After logging on one of the three front ends via ssh, user1 submits a job (job1) requesting seven compute nodes. The batch job script is sent to the head node and put in the requested queue. When the resources are available, the batch system allocates seven compute nodes and places the compute job on them.

Similarly, user3 logs on two front ends and submits two batch job scripts (job3 and job4). Both jobs request two compute nodes. During the run-time of his compute jobs, the user has access to those nodes, on which his own jobs are running.

The batch systems provide a variety of commands, both for the users and the administrators of the HPC clusters, to check ("Is my job running?") and to change the status of the jobs (for example, deleting the job).

Further information: What else do batch systems do?

#### Further information: What else do batch systems do?

Batch systems manage and monitor IT resources: They provide information about the availability of the compute nodes (free, in-use, maintenance, offline) and about the hardware-health (disks, temperature of CPUs, fan speed, ...). They log the usage ("Which user has used how many CPU hours?") and control the access to the resources.

### The Components of a Batch System: Resource Manager and Scheduler

A batch system may have one or two components: A resource manager and additionally a job scheduler.

Well-known resource managers are:
SLURM
Torque
PBSPro
Torque and PBSPro are very similar, because they are both forks of OpenPBS. PBS means: Portable Batch System.

A well-known scheduler is Moab. The Moab Cluster Suite provides more than only job scheduling: It is a cluster workload management package.

On the HPC clusters and supercomputers in Baden-Württemberg, the following batch systems are installed:

| bwUniCluster 2.0          | SLURM   |
|---------------------------|---------|
| JUSTUS                    | Moab    |
| JUSTUS II                 | SLURM   |
| MLS&WISO Development      | SLURM   |
| MLS&WISO Production       | Moab    |
| BinAC                     | Moab    |
| NEMO                      | Moab    |
| ForHLR                    | SLURM   |
| Hawk                      | PBSPro  |

Table 1: Batch systems on HPC clusters and supercomputers in Baden-Württemberg
The batch system based on Moab is explained in the next chapter The Batch System Moab.

### Overview of SLURM

The bwUniCluster 2.0, JUSTUS II and ForHLR have installed the resource manager SLURM.

SLURM (Simple Linux Utility for Resource Management) is a cluster management and job scheduling system for Linux clusters. The concept of SLURM is that jobs consist of job steps.

The most important commands are:
sbatch: submits a batch job script to the queue for later execution
srun: submits a job for immediate execution or executes single job steps in a job script (sequentially or parallel)
salloc: interactive job submission
scontrol: view and modify configuration
sinfo/smap: check nodes and partitions
sacct: get accounting data for all jobs
squeue: view job and job step information
scancel: abort job

#### Further Information: SLURM Components

The following figure shows the components of SLURM:

Die Grafik zeigt die Architektur des **SLURM-Workload-Managers**.

**User commands (links):**

- scontrol
- sinfo
- squeue
- scancel
- sacct
- srun

Diese Befehle kommunizieren mit dem Cluster-Controller.

**Controller daemons (zentral):**

- **slurmctld (primary)** – Haupt-SLURM-Controller  
- **slurmctld (backup)** – Backup-Controller
- **slurmdbd (optional)** – Datenbank-Dienst (für Accounting)  
  - kommuniziert mit einer **Database**
  - kann mit **anderen Clustern** interagieren

**Compute node daemons (unten):**

- Mehrere **slurmd**-Instanzen, je eine pro Compute-Knoten  
  Diese führen die Jobs aus, die vom slurmctld zugeteilt werden.

Ablauf:

1. User-Kommandos gehen an den **slurmctld**-Controller.
2. slurmctld weist Jobs den **slurmd**-Diensten auf den Rechenknoten zu.
3. Optional speichert slurmdbd Jobdaten in einer Datenbank.
4. Bei Ausfall übernimmt ein slurmctld-Backup.

Die Grafik verdeutlicht das Zusammenspiel der SLURM-Komponenten zwischen Benutzer, Controller und Rechenknoten.

Figure: SLURM components. Source: <https://slurm.schedmd.com/quickstart.html>
On the left, some important command line tools for users and administrators are shown (blue boxes). The yellow boxes represent SLURM components running on front ends and head node:
slurmctld: SLURM control daemon running on head node
slurmdbd: database daemon for accounting records
The green boxes denote slurmd, the compute node daemons.
Further information: SLURM-Homepage
<https://slurm.schedmd.com/quickstart.html>

## 14 The Batch System Moab

### Overview: The Batch System

In the following screencast, Karsten Siegmund (University of Ulm) explains the batch system and gives an overview of the content of the next sections.

Video Player

00:00
07:11

"The batch system - part 1" (Karsten Siegmund, University of Ulm). Lecture recording from an introductory course to bwHPC and the bwUniCluster held on 29th of June, 2015 at the University of Ulm.
Video Player

00:00
08:38

"The batch system - part 2" (Karsten Siegmund, University of Ulm). Lecture recording from an introductory course to bwHPC and the bwUniCluster held on 29th of June, 2015 at the University of Ulm.

### Resource Manager and Scheduler

In order to get access to the compute nodes, you have to request the required resources (e. g. two nodes for a walltime of three hours) from the batch system.

The batch system manages the queues, compute nodes and jobs and consists of two components: a workload manager (scheduler) and a resource manager.

The scheduler, usually MOAB is used, is in charge of job scheduling, job managing, job monitoring and job reporting.

The resource manager is responsible for the job control and for the job distribution over the compute nodes.

- On the bwUniCluster and ForHLR I, the resource manager SLURM (Simple Linux Utility for Resource Management) is used while TORQUE (Terascale Open-source Resource and QUEue Manager) is installed on the bwForClusters and ForHLR II.

This figure shows the interaction of the resource manager TORQUE/SLURM and the workload manager MOAB.

Das Bild zeigt ein schematisches Diagramm eines Ressourcen- und Workload-Managers.

Oben steht der Titel „Resource and workload manager“.
Links befindet sich ein Beispiel-Jobskript in einem grauen Kasten (#!/bin/bash mit MSUB-Optionen und einem Echo-Befehl). Daneben steht die Nummer (1) mit der Erklärung, dass der Benutzer ein Jobskript erstellt und per msub an MOAB übergibt.

In der Mitte ist ein blauer ovaler Block mit dem Text „MOAB“. Rechts daneben steht (2) mit dem Hinweis, dass MOAB das Jobskript parst und entscheidet, wo und wann der Job laufen soll.

Unterhalb von MOAB befindet sich ein großer orangefarbener Block mit der Beschriftung „compute resources: TORQUE/SLURM“. Rechts daneben steht (3), dass die Ausführung an den Ressourcenmanager auf dem Knoten delegiert wird.

Ganz unten steht (4): Der Ressourcenmanager (TORQUE/SLURM) führt den Job aus und meldet Statusinformationen an MOAB zurück.

FAQ: How many jobs can run on a single node at the same time?
This depends on the node access policy:
On "shared nodes", more than one job can run simultaneously if the requested resources are available, and these jobs may have been submitted by different users.
On "single user nodes", more than one job can run simultaneously, but the jobs have to be submitted by one and the same user.
On "single job nodes", the access is exclusive for one user, irrespective of the number of requested cores.

### Interactive Jobs and Batch Jobs

You can either start an interactive session on the compute nodes or submit your job via a batch job script to the batch system.

Interactive sessions are intended only for developing software and testing scripts, as they are not adequate for long production runs.

During an interactive session, you can enter your commands one by one, and the nodes are reserved for you for the whole requested walltime.

You must not run a compute job on the login node! Please run your jobs, even the serial ones, on the compute nodes, either in an interactive session or by submitting it via a batch job script to the batch system!

Never start a job with nohup scriptfile & or at!

Example: With the command
$ msub -I -V -l nodes=1:ppn=1,walltime=01:00:00
an interactive session for serial jobs on one node is requested for one hour. After one hour the session will be closed automatically.

The msub option -I means "interactive", and -V ensures that all environment variables are exported to the compute node.

After submission of the msub command, you have to wait a moment until the requested resources are allocated and a shell session on the compute node is started in the same terminal. Now, you can directly enter commands and start your program, e. g. with mpirun.

Batch jobs are explained on the next pages.
