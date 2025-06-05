## Introduction

GitHub Pages is a feature of GitHub that allows users to create and publish websites from their GitHub repositories.
It's a static site hosting service that can be used for
- Online blogs: Create blogs for projects
- Landing pages: Create landing pages for projects
- Personal websites: Create websites for personal use
- Portfolios: Create portfolios for personal use


### instructions

while visting website after hosting in GitHub pages , encountered below error ,

<code>
Error : 404 
the site configured at this address does not contain the requested file. if this is your site, make sure that the filename case matches the url as well as any file permissions. for root urls (like http://example.com/) you must provide an index.html file.<code>

<br>

**The solution** : move index.html to root top level of repo 

**Reasoning** : Because GitHub doesn't know to search inside of your directories for it. So you could just have your index.html open in the repo. 


### References

YT reference for hosting website in gh-pages:

https://youtu.be/57u6a_iQB8E?si=m1XlplDycvbWBL4w