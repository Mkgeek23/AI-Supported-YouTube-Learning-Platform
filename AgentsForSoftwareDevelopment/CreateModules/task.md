In this task, you'll enhance your application by implementing course module generation 
based on educational video transcripts. Before you begin, 
complete the "Agents for Software Development" course.

## **New functionality**

It's time to add new functionality to the project: 
processing educational videos and dividing them into 10-minute modules with meaningful titles based on video transcripts. 
The system should:

1. Process and structure transcript data
2. Generate module titles using an LLM API  
3. Cache the results to store course modules

Most of the code was written with AI assistance. You now need to review and complete it.

## **Task**

1. Carefully review the codebase  
2. Implement the generation of descriptive titles from transcripts using coding agent [Junie](https://www.jetbrains.com/junie/)
3. Test the code with various types of content  
4. Try different models other than `meta-llama/Llama-3.3-70B-Instruct`

### **Note**

For this task, you can optionally run an open-weight LLM locally instead of using an API. This approach is closer to installing a Python dependency into a project, but it's also a bit more challenging to implement.
