let currentVideoId = '';
let currentQuiz = null;

// Helper function to extract video_id from various YouTube URL patterns
function extractVideoId(url) {
    const patterns = [
        /v=([^&]+)/,                 // Standard YouTube URL (e.g., ?v=ID)
        /youtu\.be\/([^?&]+)/,       // Shortened YouTube URL (e.g., youtu.be/ID)
        /youtube\.com\/live\/([^?&]+)/ // YouTube Live URL (e.g., youtube.com/live/ID)
    ];
    for (const pattern of patterns) {
        const match = url.match(pattern);
        if (match) {
            return match[1]; // Return first matched group
        }
    }
    return null; // Return null if no match is found
}


// Update info display on a page load
function window_onload() {
    const urlParams = new URLSearchParams(window.location.search);
    const videoId = urlParams.get('v');
    const startTime = urlParams.get('t') || 0;

    if (videoId) {
        const url = `https://www.youtube.com/watch?v=${videoId}`;
        const urlElement = document.getElementById('currentUrl');
        urlElement.textContent = url;
        urlElement.href = url;
    }
}

function update_info(e) {
    e.preventDefault();
    const videoUrl = document.getElementById('videoUrl').value.trim();
    const startTime = document.getElementById('startTime').value || 0;

    // Extract the video_id using the helper function
    const videoId = extractVideoId(videoUrl);

    if (videoId) {
        const youtubeUrl = `https://www.youtube.com/watch?v=${videoId}&t=${startTime}`;
        const urlElement = document.getElementById('currentUrl');
        urlElement.textContent = youtubeUrl;
        urlElement.href = youtubeUrl;

        // Update iframe src directly to start playing immediately
        const iframe = document.getElementById('videoFrame');
        iframe.src = `https://www.youtube.com/embed/${videoId}?start=${startTime}&rel=0&autoplay=1`;

        // Update current video ID
        currentVideoId = videoId;
    } else {
        alert('Please enter a valid YouTube URL');
    }
}

// Quiz-related functions
async function generateQuiz(moduleTitle, difficulty = 'medium') {
    try {
        // Show processing status with progress bar
        const processingStatus = document.getElementById('processingStatus');
        const currentStep = document.getElementById('currentStep');
        const progressBar = document.getElementById('progressBar');
        const quizColumn = document.getElementById('quizColumn');

        // Reset displays
        processingStatus.style.display = 'block';
        quizColumn.innerHTML = '';

        // Update status and progress for each step
        const updateStatus = (step, progress) => {
            currentStep.textContent = step;
            progressBar.style.width = `${progress}%`;
        };

        // Start processing
        updateStatus('Preparing quiz generation...', 20);

        const response = await fetch(`/generate_quiz?video_id=${currentVideoId}&module_title=${encodeURIComponent(moduleTitle)}&difficulty=${difficulty}`);

        updateStatus('Generating quiz questions...', 60);

        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        updateStatus('Displaying quiz...', 100);

        currentQuiz = data.quiz;

        // Hide processing status after a short delay
        setTimeout(() => {
            processingStatus.style.display = 'none';
            displayQuiz(moduleTitle);
        }, 1000);
    } catch (error) {
        console.error('Error generating quiz:', error);
        document.getElementById('processingStatus').style.display = 'none';
        document.getElementById('quizColumn').innerHTML = `<div class="error-message">Error generating quiz: ${error.message}</div>`;
    }
}

function displayQuiz(moduleTitle) {
    const quizColumn = document.getElementById('quizColumn');
    if (!currentQuiz || !currentQuiz.length) {
        quizColumn.innerHTML = '<div class="error-message">No quiz questions available</div>';
        return;
    }

    let quizHtml = `
        <div class="quiz-header">
            <h3>Quiz: ${moduleTitle}</h3>
        </div>
        <div class="quiz-content">
    `;

    currentQuiz.forEach((question, index) => {
        quizHtml += `
            <div class="question" id="question_${index}">
                <p class="question-text">${index + 1}. ${question.question}</p>
                <ul class="options-list">
        `;

        Object.entries(question.options).forEach(([key, value]) => {
            quizHtml += `
                <li>
                    <input type="radio" name="q${index}" value="${key}" id="q${index}_${key}">
                    <label for="q${index}_${key}">${key}) ${value}</label>
                </li>
            `;
        });

        quizHtml += `
                </ul>
            </div>
        `;
    });

    quizHtml += `
        </div>
        <div class="quiz-footer">
            <button class="submit-quiz" onclick="submitQuiz()">Submit Answers</button>
        </div>
    `;

    quizColumn.innerHTML = quizHtml;
}

function submitQuiz() {
    if (!currentQuiz) return;

    const questions = currentQuiz;
    let score = 0;
    let totalQuestions = questions.length;

    questions.forEach((question, index) => {
        const selectedOption = document.querySelector(`input[name="q${index}"]:checked`);
        const questionDiv = document.querySelector(`#question_${index}`);
        const options = questionDiv.querySelectorAll('li');

        options.forEach(option => {
            const radio = option.querySelector('input[type="radio"]');
            const label = option.querySelector('label');

            if (radio.value === question.correct_answer) {
                option.classList.add('correct-answer');
            } else if (radio.checked && radio.value !== question.correct_answer) {
                option.classList.add('wrong-answer');
            }

            radio.disabled = true;
        });

        if (selectedOption && selectedOption.value === question.correct_answer) {
            score++;
        }
    });

    // Show score
    const scoreDiv = document.createElement('div');
    scoreDiv.className = 'quiz-score';
    scoreDiv.innerHTML = `
        <h4>Your Score: ${score}/${totalQuestions}</h4>
        <p>Correct answers are highlighted in green</p>
    `;

    const quizContent = document.querySelector('.quiz-content');
    quizContent.insertBefore(scoreDiv, quizContent.firstChild);

    // Disable submit button
    document.querySelector('.submit-quiz').disabled = true;
}
