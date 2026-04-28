Act as an expert science educator. You have created a science problem/question.

{{ question }}

Now you should do the following:
- Solve the problem.
- Estimate the difficulty of the problem. Is this problem difficult enough for a graduate student of the corresponding major? For example, if the problem is a chemistry problem, is it difficult enough for a chemistry graduate student? Is it the GPQA level difficulty? You should first write an analysis of the problem difficulty. Then give the conclusions: a) Difficulty level: (choose from easy, medium, hard or ex-hard); b) Is it GPQA-level difficulty? The answer is "yes" or "no". See the detailed output format below.
- After finishing all the above, rewrite the problem to a more difficult one.
- Try your best to keep the question concise.
- We need multi-choice questions.

### Output Format
<solution>
solution to the problem/question previous generated ...
</solution>

<analyze_difficulty>
the analysis of the difficulty of the generated problem
</analyze_difficulty>
<difficulty_conclusions>
<level>easy, medium, hard or ex-hard</level>
<gpqa_level>yes or no</gpqa_level>
</difficulty_conclusions>

<more_difficult_question>
new difficult question content (question only, not solution should be included)...
</more_difficult_question>
