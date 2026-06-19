# Clarification Questions Template

Use this before major repository changes.

## Question 1 — Goal

What is the main goal?

A. Fast implementation  
B. Clean long-term architecture  
C. Security-first audit  
D. Documentation and usability  

**Recommended: B**

## Question 2 — Risk Level

How aggressive should the agent be?

A. Read-only analysis  
B. Small safe edits  
C. Moderate implementation  
D. Large autonomous refactor  

**Recommended: B**

## Question 3 — Model Routing

Which model route should be used?

A. Local model first  
B. Cheap API model first  
C. Best available model  
D. Human-approved escalation only  

**Recommended: A for scouting, C for final architecture**

## Question 4 — Output Format

What should the agent produce?

A. Plan only  
B. Patch/diff  
C. Full implementation  
D. Audit report  

**Recommended: A before B**
