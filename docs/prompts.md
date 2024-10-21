# CodeQuery Prompts

## Translation

```
Traduza essa response para o português.
```

## Development

```
Outline the next steps and proceed with the most appropriate one(s).
```

```
Proceed. But first, query the project structure.
```

```
TASK/FEATURE

Query the relevant file(s) in order to perform this task.

Query the relevant file(s) in order to implement this.
```

```
TASK/FEATURE

Before responding, query the project structure, then query all relevant files in order to (perform this task / implement this).
```

```
Now i want to implement this feature:

> Sort the technologies of output in alphabetic order.

Query the project structure, then query all relevant files needed in order to implement this.
```

```
PROMPT

Remember to always query the relevant file(s) before responding.
```

## Notes

```
Note: Always query the relevant file(s) before suggesting code changes or new code.

Note: Always query the working file(s) before suggesting code changes.

Note: Query the project structure to refresh your memory
```

## Debugging

```
Console error:
"""
"""

Query the project structure, then query the relevant files in order to suggest a fix.
```

```
Error:
""""""

Still the same issue. Query relevant files in order to suggest a fix (at least 3 files).
```

```
Error:
""""""

Query the relevant files in order to suggest a fix.
```

```
Error:
"""
"""

Query the tested file, the test file, and, if necessary, other files that may be useful to debug the error. (Query at least 2 files.)
```

```
Well done! Now to the next error...

Still getting error. Follow this CoT again:

1 test still failing. Follow this CoT:

- Query and analyse the last test results (tests/results.txt).
- Analyse the test results.
- Query all files that may be useful to debug the error.
- Suggest a fix to the error.
```

```
One more test passed. Congrats!

1 of the 2 failures solved. Congrats!

Now follow this CoT again for the last failure:

We're getting errors. Follow this CoT:

We got an error. Follow this CoT:

1 test still failing. Follow this CoT:

- Query and analyse the last test results (tests/results.txt).
- Query the tested file, the test file, and, if necessary, other files that may be useful to debug 1 or 2 errors.
- Suggest a fix to this 1 or these 2 errors.
```

```
A different error now. Follow this CoT again:

- Query the last test results (gateway/tests/results.txt).
- Analyse them.
- Query the relevant file(s) in order to fix 1 or more errors.
- Suggest a fix to this error(s).
```

```
Query the test results. Analyse them. Then query all relevant files in order to suggest a fix.
```

```
We st... Repeat the process: Query the test results. Analyse them. Then query all relevant files in order to suggest a fix.
```

```
Query the test results. Then query the project structure to refresh your memory. Finally, query the relevant files in order to suggest a fix.
```

```
Follow this CoT:

- Deeply analyse the CL output above.
- After the analysis, query the relevant file(s) that may help to solve the issue(s).
- Then attempt to solve the issue(s).
```

```
Output:
"""
"""

Follow this CoT again:

- Query Core logs (logs/journalctl.txt) and Gateway logs (gateway/logs/journalctl.txt)
- Analyse them.
- After the analysis, query the relevant file(s) that may help to solve the issue(s).
- Analyse this files, aiming to solve the issue.
- Finally, attempt to solve the issue(s).
```

## Persistent Error Loop

```
Let's stop and think on a different approach to test the required behavior of gateway.py. Looks like the current approach for some reason is stuck on a "permanent" issue loop.

Don't forget to query all relevant files for the task.
```

## Analysis

```
[...]

First, analyse the situation. Then, ask for my opinion. Then, query all the relevant files in order to suggest a fix.
```

## Prompt Improvement

```
First, improve this prompt:
"""
"""
Then, respond it.
```

## Economics

```
Please outline our next steps to finalize the Markdown versions of the paper and appendices, focusing on writing any sections or appendices that haven't been completed yet. Then, proceed with the most appropriate next step.
```

```
Please proceed with the next appropriate steps to finalize the paper and appendices, focusing on completing any remaining sections and optimizing the number of steps in your response for efficiency.
```

```
Please provide an overview of the current status of the article and appendices in their Markdown format, including the completion status for each section. Then, proceed with the next appropriate steps to finalize the paper and appendices, focusing on completing any remaining sections and optimizing your response for efficiency.
```

## Code Optimization

```
Suggest improvements to the current code base in order to enhance performance.
```

```
Refactor this function to improve readability and maintainability.
```

## Testing & Validation

```
Write test cases to validate the correctness of the following function:
[insert function]
```

## Agent KT (pending)

```
This chat is getting heavy and slow. I want to start a chat with a new CodeQueryGPT agent. Write a KT prompt to pass the current context to it.
```
