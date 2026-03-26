# Introduction

Remote desktops help to centralize key software and optimize usage among a team.

### In option 1 (Park Ten)

- The server is located in the office.

User1  and User2 are sharing the server. We want to understand how it works with respect to sharing the server resources (i.e. Hardware, data and license). Please see a scenario that we tried this morning:
Step 1: User1 was logged in and running Orcaflex with 24 logical processors (Max logical processors available are 32). User1 locked the computer.
Step 2: User2 was able to log-in and run OrcaFlex with additional 11 logical processors.

Key questions that we can guess but my limited knowledge & logic was defeating us a bit. Please help us understand more.

a/ Only 1 person can login at a time. But can multiple persons login and still view data in their own way (impossible as there is only 1 graphics card? or can it work like virtual machines in cloud?).
b/ We thought OrcaFlex can run only 32 logical processors at max at hardware capacity. But in above scenario, 35 may be running. Is it possible?
c/ Is it utilizing the same OrcaFlex license or is it using 2 different licenses for each user?
d/ Are we slowing our runs with this 2 user concurrent usage?
e/ Is there a way to access data over the network while the other user is loggedin running and accessing the server.

### In option 2 (Barker Cypress)

User1 and User2 are sharing the server.
a/ They share the VPN and see the same view.

Things are clear as it is sharing the same view, same computer etc.
