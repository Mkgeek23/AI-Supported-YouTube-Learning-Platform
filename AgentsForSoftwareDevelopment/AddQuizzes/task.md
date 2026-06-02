The quiz generation feature now allows users to generate and take quizzes based on video content. 
Each module has a dedicated quiz button that generates questions specific to that module's content.

## **Features**

* Each module displays a "Quiz" button.  
* Clicking the button generates module-specific questions.  
* Questions are automatically generated based on module content.  
* Multiple-choice format with immediate feedback.

## **API endpoint**
Generates quiz questions for a specific module.

```
GET /generate_quiz?video_id={video_id}&module_title={module_title}&difficulty={difficulty}
```

## **Usage instructions**
1. Load a video using the YouTube URL input.  
2. Click `To modules` to view the video modules.  
3. For any module, click the `Quiz` button to generate questions.  
4. Answer the multiple-choice questions.  
5. Click `Submit Answers` to see your score and correct answers.

## **Task**
Just try out the app, generate quizzes for some video from YouTube, 
and enjoy the code you wrote in collaboration with AI!
