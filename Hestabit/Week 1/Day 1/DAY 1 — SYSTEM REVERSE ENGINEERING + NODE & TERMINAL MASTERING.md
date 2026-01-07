## 
### Learning Outcomes
- Master terminal navigation and system inspection
- Deep understanding of PATH, environment variables, Node runtime
### Tasks (**NO GUI allowed — only terminal**)

1. **Identify and document:** 
    - OS version
    - Current shell (**bash / zsh / powershell**)
    - Node binary path (`which node`)
    - NPM global installation path
    - All PATH entries that include `"node"` or `"npm"`
2. **Install & use NVM (Node Version Manager):**
    - Install NVM
    - Switch Node from **LTS → Latest** and back
3. **Create script `introspect.js` that prints:**

`OS: Architecture: CPU Cores: Total Memory: System Uptime: Current Logged User: Node Path:`
### 4. **STREAM vs BUFFER exercise (performance benchmark)**

- Create a large test file (**50MB+**)
- Read file using both:
    - `fs.readFile` (**Buffer**)
    - `Stream` (`fs.createReadStream`)
- Capture **execution time + memory usage**
    

---

### **Deliverables**

|Deliverable|Format|
|---|---|
|`system-report.md`|Document with screenshots|
|`introspect.js`|JS script|
|`logs/day1-perf.json`|Execution time + memory usage|
|`commits`|_(Minimum 6 commits with meaningful messages)_|

---

## MY PART 
### GIT AND NVM SETUP
sudo apt update 
sudo apt upgrade
sudo apt install curl 
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.1/install.sh | bash
sudo apt install libfuse2
nvm --version

resource :- https://www.geeksforgeeks.org/linux-unix/how-to-install-nvm-on-ubuntu-22-04/
https://www.geeksforgeeks.org/linux-unix/how-to-install-nvm-on-ubuntu-22-04/


INSTROSPECT.JS
![[Pasted image 20260106180913.png]]

![[Pasted image 20260106180925.png]]


