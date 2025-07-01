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

### Multiple User Login (Shared Resources)

- Example: ANS 01 thru 04
- Utilizes windows server loging to allow logging of multiple users


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

    subgraph "User1 on Server (Half-resources, 1-license)"
        CPU_user2_1["Run OrcaFlex Dynamics<br/>Using Np Processors"]
        Memory_user2_1["Process Power/2 <br/>Memory/2<br/>Memory/2<br/>Disk/2"]
        Software_user2_1["Software License i.e. OrcaFlex"]
        Data_user2_1["**Data**"]

    end

    subgraph "User2 on same Server (Half-resources, additional license)"
        CPU_user2_2["Additional OrcaFlex Dynamics<br/>Using Np Processors"]
        Memory_user2_2["Process Power/2 <br/>Memory/2<br/>Memory/2<br/>Disk/2"]
        Software_user2_2["Additional Software License i.e. OrcaFlex"]
        Data_user2_2["**Data**"]

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