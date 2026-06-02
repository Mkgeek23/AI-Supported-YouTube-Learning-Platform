In this task, you'll generate a detailed technical project specification using prompting techniques. 
Before getting started, complete the "Prompting Techniques" course.

## Task
Watch this video for step-by-step guidance:
 - [Task 1: Prompting Techniques](https://www.youtube.com/watch?v=d3D9ASVBzMc)

### 1. Evironment setup
First, you need to set up your environment by creatig an API key. Here's how you do that:
1. Generate an API key at: https://studio.nebius.com/settings/api-keys
2. In your project root, create a `.env` file: right-click on "AI-Supported YouTube Learning Platform" → New → File → .env
3. Add the following line to your .env file and save your API key to the variable:
```shell
   NEBIUS_API_KEY=<your-api-key-here>
```

4. Verify the file content by running the following command in the PyCharm Terminal:
```shell
   cat .env
```

You'll use API calls to work with LLMs throughout the project. It's essential for several reasons:
 * **Automation**: APIs allow the application to interact with AI models programmatically.
 * **Integration**: You can integrate AI capabilities directly into the development workflow.
 * **Scalability**: APIs handle multiple requests efficiently and can be scaled based on needs.
 * **Security**: API keys help manage access and usage tracking.

### 2. Generating the technical specification

1. Create a Markdown file named `student_specification.md`. It will store your project specification.  
2. To generate the initial version of the specification, run [./task.py](file://PromptingTechniques/SpecGeneration/task.py) in PyCharm. Then refine it by using prompting techniques and adjusting LLM parameters.  
   The project you will be developing is a YouTube-based learning platform with the following core features:  
   * A YouTube video player  
   * A video transcriber  
   * A quiz generator  
3. Your final specification should include the following sections:  
   * Project Overview & Requirements  
   * Architecture & Data Modeling  
   * Implementation Strategy  
   * Testing & Quality Assurance  
   * Deployment & Security  
4. You should:  
   * **Follow a clear structure**: Use headings and subheadings to organize information. Start broad and narrow down to specifics.  
   * **Include implementation details**: Specify tools, frameworks, data models, relationships, API endpoints, and features.  
   * **Highlight AI integration points**: Identify where and how AI will be used, describe AI agent roles and responsibilities, and include example prompts for specific tasks.  
   * **Incorporate visual elements**: Add diagrams where they would be helpful.  
5. When you're ready, click the "Check" button below. `Llama-3.3-70B-Instruct` will evaluate your submission on:  
   * Clarity and completeness of the project description.  
   * Practical applicability of the AI integration points.  
   * Technical accuracy and feasibility of the proposed solution.

## **Tips for success**

* Use specific, actionable language in your prompts.  
* Include context and constraints in your requests.  
* Break down complex sections into smaller, focused prompts.  
* Review and refine AI-generated content for accuracy.  
* Maintain consistency across all sections.
