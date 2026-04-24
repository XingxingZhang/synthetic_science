Act as an expert science educator and create a new question and its solution based on the provided topics and key concepts. Ensure that the created questions:
1. Adhere to the provided topics.
2. Necessitate the combined use of the associated key concepts.
3. If there are equations, please use latex format

{{ few_shot_train_examples }}

{{ my_example }}

Try to create a science question according to the topics and key concepts for the last one.

### Requirements
- Note that you should ONLY output the question and do not include the solution. 
- Do not generate the type of questions the options are four (or > four) different statements and asks the student to judge which of them are correct/wrong. We have statement judgement type questions already. DO NOT generate questions contains phrases like "Which of the following ...", "Which option correctly states ...". 
- We need question which needs strong reasoning and/or computations to get the correct answers
- DO NOT give hints to in the question. for example, do NOT state which key concepts should be use to solve the problem. I want to test the abilities of students on using learned knowledge flexibly. For example, phrase such as "Using the reading-frame logic and the role of exon skipping in antisense therapy to ..." is not allowed. Because, you are giving hints that key concepts "reading-frame logic" and "the role of exon skipping in antisense therapy" are helpful to solve the question.
- Try your best to keep the question concise.
- Make the question as difficult as possible. We are trying to create questions for graduate students of the biology, physics, or chemistry majors. For example, if the question is an physics problem, it should be difficult for an physics major graduate student to solve it.
- We need multi-choice questions.

## Output Format
<question>
question content (question only, not solution should be included)...
</question>

## Output