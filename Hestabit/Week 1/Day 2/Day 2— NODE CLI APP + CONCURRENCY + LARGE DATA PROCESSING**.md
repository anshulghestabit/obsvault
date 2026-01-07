## **AY 2 

### Learning Outcomes

- Asynchronous programming
	- CLI tool building
	- Concurrency + performance measurement
   

### Tasks

 1. **Generate a corpus text file** with **200,000+ words**  
    _(random lorem or internet scrape)_
2. **Build CLI command:**
`node wordstat.js --file corpus.txt --top 10 --minLen 5 --unique`

4. **The CLI must output:**
- Total words
- Unique words
- Longest word
- Shortest word
- Top N most repeated words

4. **Implement concurrency:**
- Divide file into chunks
- Process chunks in parallel using:
    - `Promise.all` **or**
    - `worker_threads`
4. **Benchmark performance for concurrency levels:**
    - Concurrency **1, 4, 8**
    - Capture runtime performance in logs
    
---

### Deliverables

| Deliverable              | Format                                     |
| ------------------------ | ------------------------------------------ |
| `wordstat.js`            | Executable CLI tool                        |
| `output/stats.json`      | Final computed results                     |
| `logs/perf-summary.json` | Concurrency test with runtime              |
| `commits`                | Minimum **8 commits** documenting progress |



# my deliverables
## task 1
### installing pandoc for file parsing and viewing
resource:- https://www.geekyhacker.com/how-to-open-formatted-markdown-files-in-linux-terminal/


got book from bookbot course boot.dev 
resource:- https://storage.googleapis.com/qvault-webapp-dynamic-assets/course_assets/frankenstein.txt
command :- wget  -o ../frankenstein.txt https://storage.googleapis.com/qvault-webapp-dynamic-assets/course_assets/frankenstein.txt
command to check word count :- wc -w frankenstein.txt
course:- https://www.boot.dev/lessons/3e0113f5-18a9-4b4a-9600-6b9b928c01ac
![[Pasted image 20260107142532.png]]![[Pasted image 20260107142610.png]]'