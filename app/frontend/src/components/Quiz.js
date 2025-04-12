import React, { useState } from 'react';
import { Button } from './ui/button';
import { RadioGroup, RadioGroupItem } from './ui/radio-group';
import { Label } from './ui/label';

const Quiz = ({ questions, onComplete, onClose }) => {
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [showResults, setShowResults] = useState(false);
  const [score, setScore] = useState(0);

  const handleAnswerSelect = (questionId, answer) => {
    setSelectedAnswers({
      ...selectedAnswers,
      [questionId]: answer
    });
  };

  const handleNext = () => {
    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    } else {
      // Calculate score
      let correctCount = 0;
      questions.forEach(question => {
        if (selectedAnswers[question.id] === question.correctAnswer) {
          correctCount++;
        }
      });
      
      setScore(correctCount);
      setShowResults(true);
      
      // Pass results to parent
      onComplete({
        totalQuestions: questions.length,
        correctAnswers: correctCount,
        score: (correctCount / questions.length) * 100
      });
    }
  };

  const currentQuestionData = questions[currentQuestion];

  if (showResults) {
    return (
      <div className="bg-card rounded-lg border border-border p-6 shadow-md transition-colors duration-300">
        <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
          <span role="img" aria-label="results" className="text-2xl">🏆</span> 
          Quiz Results
        </h2>
        
        <div className="mb-6 p-4 bg-muted rounded-lg">
          <p className="text-lg mb-2">
            You scored: <span className="font-bold">{score}</span> out of {questions.length}
          </p>
          <div className="w-full bg-primary/20 rounded-full h-4 mb-2">
            <div 
              className="bg-primary h-4 rounded-full" 
              style={{ width: `${(score / questions.length) * 100}%` }}
            ></div>
          </div>
          <p className="text-sm text-muted-foreground">
            {(score / questions.length) >= 0.8 
              ? "Great job! You have a solid understanding of the material." 
              : (score / questions.length) >= 0.6 
                ? "Good work! You're on the right track." 
                : "Keep learning! Review the document to improve your understanding."}
          </p>
        </div>
        
        <div className="space-y-4 mb-6">
          <h3 className="font-semibold">Review your answers:</h3>
          {questions.map((question, index) => (
            <div 
              key={question.id} 
              className={`p-4 rounded-lg border ${
                selectedAnswers[question.id] === question.correctAnswer
                  ? "border-green-500 bg-green-50 dark:bg-green-950/20"
                  : "border-red-500 bg-red-50 dark:bg-red-950/20"
              }`}
            >
              <p className="font-medium mb-2">{index + 1}. {question.text}</p>
              <p className="text-sm">
                Your answer: <span className={`font-medium ${
                  selectedAnswers[question.id] === question.correctAnswer
                    ? "text-green-600 dark:text-green-400"
                    : "text-red-600 dark:text-red-400"
                }`}>
                  {selectedAnswers[question.id] || "Not answered"}
                </span>
              </p>
              {selectedAnswers[question.id] !== question.correctAnswer && (
                <p className="text-sm mt-1">
                  Correct answer: <span className="font-medium text-green-600 dark:text-green-400">
                    {question.correctAnswer}
                  </span>
                </p>
              )}
            </div>
          ))}
        </div>
        
        <div className="flex justify-end">
          <Button onClick={onClose}>
            Back to Chat
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-card rounded-lg border border-border p-6 shadow-md transition-colors duration-300">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <span role="img" aria-label="quiz" className="text-2xl">📝</span> 
          Knowledge Quiz
        </h2>
        <span className="text-sm bg-primary/10 px-3 py-1 rounded-full">
          Question {currentQuestion + 1} of {questions.length}
        </span>
      </div>

      <div className="mb-8">
        <h3 className="text-lg font-medium mb-4">{currentQuestionData.text}</h3>
        
        <RadioGroup 
          value={selectedAnswers[currentQuestionData.id] || ''}
          onValueChange={(value) => handleAnswerSelect(currentQuestionData.id, value)}
          className="space-y-3"
        >
          {currentQuestionData.options.map((option) => (
            <div key={option} className="flex items-center space-x-2 p-3 rounded-lg border border-border hover:bg-muted/50 transition-colors">
              <RadioGroupItem value={option} id={`option-${option}`} />
              <Label htmlFor={`option-${option}`} className="flex-1 cursor-pointer">{option}</Label>
            </div>
          ))}
        </RadioGroup>
      </div>
      
      <div className="flex justify-between">
        <Button 
          variant="outline"
          onClick={onClose}
        >
          Cancel Quiz
        </Button>
        
        <Button 
          onClick={handleNext}
          disabled={!selectedAnswers[currentQuestionData.id]}
        >
          {currentQuestion < questions.length - 1 ? 'Next Question' : 'Finish Quiz'}
        </Button>
      </div>
    </div>
  );
};

export default Quiz; 