<<<<<<< Updated upstream
# REMOTE ACCESS: SHARED vs SIMULTANEOUS LOGIN

Last updated: 2026-02-11

## Overview

There are two ways to share a remote workstation among multiple engineers: common login (shared desktop) or simultaneous login (separate desktops). The right choice depends on how many software licenses are available and whether users need separate desktops.

## Comparison

| Aspect | Common Login (TightVNC) | Simultaneous Login (Windows Server RDP) |
|--------|-------------------------|----------------------------------------|
| Users at once | 1 (shared desktop) | 2+ (separate desktops) |
| OS required | Windows 11 is fine | Windows Server 2022 |
| Resources per user | Full machine | Split (halved for 2) |
| Licenses needed | 1 | 1 per running instance |
| Confidentiality | None (shared view) | Per-user desktop |
| Software examples | TightVNC (free) | RDP (built into Server) |
| Cost | Free | Server license cost |

**RECOMMENDATION:**
- Common login via TightVNC for single-license software (OrcaFlex)
- Simultaneous login via RDP for multi-license software (ANSYS)

## Architecture Diagram

```mermaid
flowchart LR
    subgraph Engineers
        E1[Engineer 1]
        E2[Engineer 2]
        E3[Engineer 3]
    end

    subgraph "Common Login - TightVNC"
        VNC[ACMA-ANSYS05\nOrcaFlex Workstation]
    end

    subgraph "Simultaneous Login - RDP"
        RDP1[ACMA-ANSYS01\nANSYS Workstation]
        RDP2[ACMA-ANSYS02\nANSYS Workstation]
    end

    E1 -- "TightVNC\n(1 at a time)" --> VNC
    E1 -- "RDP Session 1" --> RDP1
    E2 -- "RDP Session 2" --> RDP1
    E3 -- "RDP Session 1" --> RDP2
    E2 -.->|"blocked while\nE1 connected"| VNC
```

## Common Login (TightVNC) — How It Works

- One shared account on the workstation (e.g., shared OrcaFlex user)
- All users connect to the SAME desktop session via TightVNC
- Only one person operates the machine at a time
- Full machine resources available to that one user
- Only one software license consumed at a time
- No privacy — everyone sees the same screen

> Use for: OrcaFlex (single-seat license on ACMA-ANSYS05)

## Simultaneous Login (Windows Server RDP) — How It Works

- Each user has their own Windows account
- Multiple users can log in at the same time via RDP
- Each user gets their own desktop session
- Machine resources (CPU, RAM, disk) are split between users
- Each running software instance consumes its own license
- Full privacy — each user sees only their own desktop

> Use for: ANSYS products on ACMA-ANSYS01 through ACMA-ANSYS04

## Frequently Asked Questions

**Q: Can multiple users run OrcaFlex simultaneously?**
A: Only if you have additional OrcaFlex licenses. ACMA currently has one seat. Two users cannot run OrcaFlex at the same time with one license, regardless of the login method.

**Q: Does simultaneous login slow down analysis runs?**
A: Yes. With 2 users logged in, each gets roughly half the CPU cores and half the RAM. A run that takes 4 hours solo may take 7-8 hours with two users active. The exact slowdown depends on the analysis type and how resource-intensive both sessions are.

**Q: If two users are logged in simultaneously, does that use 1 or 2 software licenses?**
A: It depends on how many instances of the software are running. Each running instance of OrcaFlex or ANSYS consumes one license, regardless of how the user logged in. Two users each running OrcaFlex = 2 licenses needed. One user running OrcaFlex and another user doing file management = 1 license.

**Q: Can I access data on the server while another user is running an analysis?**
A: Yes. You can access shared drives and file shares over the network without needing to log in to the server. Only use RDP/VNC when you need to run software that requires the server's hardware or license.

**Q: What happens if I lock the screen via common login?**
A: On TightVNC (common login), locking the screen means the next person who connects via VNC will see the lock screen. They need the shared credentials from the company password manager to unlock.

**Q: Can I use RDP instead of TightVNC for OrcaFlex?**
A: Technically yes, but not recommended. RDP creates a new session and may not see the existing TightVNC session. Stick with TightVNC for the OrcaFlex workstation to avoid confusion.

## Current ACMA Setup

| Machine | Access Method | Purpose |
|---------|---------------|---------|
| ACMA-ANSYS05 | TightVNC | OrcaFlex (single-seat license) |
| ACMA-ANSYS01 | RDP | ANSYS workstation |
| ACMA-ANSYS02 | RDP | ANSYS workstation |
| ACMA-ANSYS04 | RDP | ANSYS workstation |
| ACMA-WS011 | RDP | General workstation |

> **NOTE:** Credentials for all machines are in the company password manager. Contact IT for access. Do not store passwords in documents.

## Related Documents

| Document | Location |
|----------|----------|
| OrcaFlex license usage guide (connection, etiquette, troubleshooting) | acma-projects/admin/orcaflex/use_instructions.md |
| Remote desktop machine list and VPN access | acma-projects/admin/acma_vpn.md |
| Licensed software inventory and cost reduction recommendations | acma-projects/admin/licensed_software_review.md |
=======
## Summary

- **Solution** : Shared username (eg: orcaflex, ansys etc.)/password pair to login and logout.
  - tightVPN (currently on OrcaFlex server)

## Details

### Common User Login

- Example: ANS 05
- Shared username/password
- **Full Transperency and Trust**
- Example software solutions:
  - tightVPN (free)
  - splashtop (USD 10/mo/user)
  - TeamViewer (USD 25/mo for 3 devices), etc.
- Cons: **No confidentiality**

### Simultaneous User Login (Shared Resources)

- Example: ANS 01 thru 04
- Utilizes windows server loging to allow logging of multiple users. For 2 user simultaneous login case study:
  - Resources are halved
  - Licenses are (not shared) doubled

- Important Considerations For multiple users:
    - It is important to close all licensed software 
    and log-out in the following example scenarios: 
    - When user licensed software runs are done (even after a day or Monday)
    - When user licensed software is going to be unused for more than 1 hour duration
    - Should not keep open to just block/hoard license unless there is an urgency.

## Common vs. Multiple

```mermaid
flowchart TD
    subgraph "Server Resources"
        CPU["**CPU**<br/>Nc Cores<br/>Np Processors"]
        Memory["Process Power <br/>Memory<br/>Disk"]
        Software["Software License i.e. OrcaFlex"]
        Data["**Data**"]
        OS["Windows Server 2022 Required"]
    end

    subgraph "Common User Login"
        CPU_user1["Run OrcaFlex Dynamics<br/>Using Np Processors"]
        Memory_user1["Process Power <br/>Memory<br/>Disk"]
        Software_user1["Software License i.e. OrcaFlex"]
        Data_user1["**Data**"]
        OS["Windows 11 Sufficient"]
    end

    subgraph "Simultaneous User2 on same Server (Half-resources, additional license)"
        CPU_user2_2["Additional OrcaFlex Dynamics<br/>Using Np Processors"]
        Memory_user2_2["Process Power/2 <br/>Memory/2<br/>Memory/2<br/>Disk/2"]
        Software_user2_2["Additional Software License i.e. OrcaFlex"]
        Data_user2_2["**Data**"]

    end

    subgraph "User1 on Server (Half-resources, 1-license)"
        CPU_user2_1["Run OrcaFlex Dynamics<br/>Using Np Processors"]
        Memory_user2_1["Process Power/2 <br/>Memory/2<br/>Memory/2<br/>Disk/2"]
        Software_user2_1["Software License i.e. OrcaFlex"]
        Data_user2_1["**Data**"]

    end


    

    CPU --> CPU_user1
    Memory --> Memory_user1
    Software --> Software_user1
    Data --> Data_user1

    CPU_user1 --> CPU_user2_1
    Memory_user1 --> Memory_user2_1
    Software_user1 --> Software_user2_1
    Data_user1 --> Data_user2_1

    CPU_user1 --> CPU_user2_2
    Memory_user1 --> Memory_user2_2
    Software_user1 --> Software_user2_2
    Data_user1 --> Data_user2_2

    classDef title fill:#ff6347,stroke:#ff0000,stroke-width:2px
    classDef note fill:#ffffcc,stroke:#666,stroke-width:1px

```
>>>>>>> Stashed changes
