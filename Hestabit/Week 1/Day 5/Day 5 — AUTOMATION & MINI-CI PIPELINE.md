## **DAY 5**
### Learning Outcomes
- Automation mindset
   - Build safeguards to prevent bad commits
### Tasks
1. **Create `validate.sh` script**
       - Ensure `src/` exists
    - Ensure `config.json` is valid
    - Append logs with timestamps
2. **Add ESLint + Prettier**
       - Bad formatting must block commit
3. **Add pre-commit hook using Husky**
       - Runs `lint`, `validate.sh`
    - Reject commit if script fails
4. **Create build artifact**
       - `build-<timestamp>.tgz`
    - Include logs + source code
    - Generate SHA checksum
5. **Schedule script execution**
      - `cron` (Linux/macOS) or
    - Task Scheduler (Windows)
---
### Deliverables

| Deliverable                   | Format                       |
| ----------------------------- | ---------------------------- |
| `validate.sh`                 | Must exit non-zero on error  |
| `.eslintrc` + Prettier config | Required                     |
| Husky hook screenshot         | Must show failed commit      |
| `artifacts/build-*.tgz`       | Evidence of packaging        |
| `WEEK1-RETRO.md`              | Lessons learned & what broke |
