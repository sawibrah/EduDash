// Code Editor functionality with Monaco Editor
class CodeEditorManager {
    constructor() {
        this.editor = null;
        this.language = 'python';
        this.theme = 'vs-dark';
        this.autoSaveInterval = null;
        this.lastSavedContent = '';
    }

    // Initialize Monaco Editor
    async initEditor(elementId, initialCode = '', language = 'python') {
        this.language = language.toLowerCase();
        
        // Load Monaco Editor from CDN
        if (!window.monaco) {
            await this.loadMonacoEditor();
        }

        // Configure Monaco Editor
        this.editor = window.monaco.editor.create(document.getElementById(elementId), {
            value: initialCode,
            language: this.getMonacoLanguage(language),
            theme: this.theme,
            automaticLayout: true,
            fontSize: 14,
            lineNumbers: 'on',
            roundedSelection: false,
            scrollBeyondLastLine: false,
            readOnly: false,
            minimap: { enabled: false },
            wordWrap: 'on'
        });

        // Setup auto-save
        this.setupAutoSave();
        
        return this.editor;
    }

    // Load Monaco Editor from CDN
    async loadMonacoEditor() {
        return new Promise((resolve, reject) => {
            // Create script element for Monaco loader
            const loaderScript = document.createElement('script');
            loaderScript.src = 'https://cdn.jsdelivr.net/npm/monaco-editor@0.44.0/min/vs/loader.js';
            
            loaderScript.onload = () => {
                require.config({ 
                    paths: { 
                        vs: 'https://cdn.jsdelivr.net/npm/monaco-editor@0.44.0/min/vs' 
                    } 
                });
                
                require(['vs/editor/editor.main'], () => {
                    resolve();
                });
            };
            
            loaderScript.onerror = () => {
                reject(new Error('Failed to load Monaco Editor'));
            };
            
            document.head.appendChild(loaderScript);
        });
    }

    // Map programming languages to Monaco language IDs
    getMonacoLanguage(lang) {
        const languageMap = {
            'python': 'python',
            'javascript': 'javascript',
            'java': 'java',
            'cpp': 'cpp',
            'c++': 'cpp',
            'c#': 'csharp',
            'csharp': 'csharp',
            'ruby': 'ruby',
            'go': 'go',
            'rust': 'rust',
            'php': 'php',
            'swift': 'swift',
            'kotlin': 'kotlin',
            'scala': 'scala',
            'typescript': 'typescript'
        };
        
        return languageMap[lang.toLowerCase()] || 'plaintext';
    }

    // Get starter code templates for different languages
    getStarterCode(language, problemType = 'basic') {
        const templates = {
            'python': `# Write your Python code here
def solve():
    # Your solution goes here
    pass

# Test your function
result = solve()
print(result)
`,
            'javascript': `// Write your JavaScript code here
function solve() {
    // Your solution goes here
    return null;
}

// Test your function
const result = solve();
console.log(result);
`,
            'java': `public class Solution {
    public static void main(String[] args) {
        Solution sol = new Solution();
        // Test your solution
        System.out.println(sol.solve());
    }
    
    public Object solve() {
        // Your solution goes here
        return null;
    }
}
`,
            'cpp': `#include <iostream>
#include <vector>
#include <string>

using namespace std;

class Solution {
public:
    void solve() {
        // Your solution goes here
        cout << "Hello, World!" << endl;
    }
};

int main() {
    Solution sol;
    sol.solve();
    return 0;
}
`,
            'c#': `using System;

public class Solution 
{
    public static void Main(string[] args) 
    {
        Solution sol = new Solution();
        sol.Solve();
    }
    
    public void Solve() 
    {
        // Your solution goes here
        Console.WriteLine("Hello, World!");
    }
}
`
        };
        
        return templates[language.toLowerCase()] || `// Write your ${language} code here\n\n`;
    }

    // Setup auto-save functionality
    setupAutoSave() {
        if (!this.editor) return;
        
        // Save every 30 seconds
        this.autoSaveInterval = setInterval(() => {
            this.autoSave();
        }, 30000);
        
        // Save on content change (debounced)
        let saveTimeout;
        this.editor.onDidChangeModelContent(() => {
            clearTimeout(saveTimeout);
            saveTimeout = setTimeout(() => {
                this.autoSave();
            }, 2000);
        });
    }

    // Auto-save code to localStorage
    autoSave() {
        if (!this.editor) return;
        
        const content = this.editor.getValue();
        if (content !== this.lastSavedContent) {
            const quizId = document.getElementById('quiz-id')?.value;
            if (quizId) {
                localStorage.setItem(`quiz_${quizId}_code`, content);
                this.lastSavedContent = content;
                this.updateSaveStatus('Auto-saved');
            }
        }
    }

    // Load saved code from localStorage
    loadSavedCode(quizId) {
        const savedCode = localStorage.getItem(`quiz_${quizId}_code`);
        if (savedCode && this.editor) {
            this.editor.setValue(savedCode);
            this.lastSavedContent = savedCode;
        }
        return savedCode;
    }

    // Update save status indicator
    updateSaveStatus(message) {
        const statusElement = document.getElementById('save-status');
        if (statusElement) {
            statusElement.textContent = message;
            statusElement.className = 'text-success small';
            
            // Clear after 3 seconds
            setTimeout(() => {
                statusElement.textContent = '';
            }, 3000);
        }
    }

    // Get current code content
    getCode() {
        return this.editor ? this.editor.getValue() : '';
    }

    // Set code content
    setCode(code) {
        if (this.editor) {
            this.editor.setValue(code);
        }
    }

    // Change editor language
    changeLanguage(language) {
        if (this.editor) {
            const model = this.editor.getModel();
            window.monaco.editor.setModelLanguage(model, this.getMonacoLanguage(language));
            this.language = language;
        }
    }

    // Run code (placeholder - would need backend integration)
    async runCode() {
        const code = this.getCode();
        const runButton = document.getElementById('run-code-btn');
        const outputElement = document.getElementById('code-output');
        
        if (!code.trim()) {
            this.showOutput('Error: No code to run', 'error');
            return;
        }

        // Show loading state
        if (runButton) {
            runButton.disabled = true;
            runButton.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Running...';
        }

        try {
            // This would make an API call to run the code
            // For now, just simulate execution
            this.showOutput('Code execution would happen on the backend...', 'info');
            
            // Simulate processing time
            await new Promise(resolve => setTimeout(resolve, 1000));
            
        } catch (error) {
            this.showOutput(`Error: ${error.message}`, 'error');
        } finally {
            // Reset button state
            if (runButton) {
                runButton.disabled = false;
                runButton.innerHTML = '<i class="fas fa-play me-1"></i>Run Code';
            }
        }
    }

    // Submit code
    async submitCode(quizId) {
        const code = this.getCode();
        const submitButton = document.getElementById('submit-code-btn');
        
        if (!code.trim()) {
            alert('Please write some code before submitting.');
            return;
        }

        // Show loading state
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Submitting...';
        }

        try {
            // Get CSRF token from meta tag or form
            const csrfToken = document.querySelector('input[name="csrf_token"]')?.value || 
                            document.querySelector('meta[name="csrf-token"]')?.content;
            
            const response = await fetch(`/quiz/${quizId}/submit`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    code: code,
                    language: this.language
                })
            });

            const result = await response.json();
            
            if (result.success) {
                // Clear auto-saved code
                localStorage.removeItem(`quiz_${quizId}_code`);
                
                // Show success message
                alert('Code submitted successfully!');
                
                // Optionally redirect or update UI
                if (result.redirect) {
                    window.location.href = result.redirect;
                }
            } else {
                alert(result.message || 'Submission failed. Please try again.');
            }
            
        } catch (error) {
            alert('Network error. Please check your connection and try again.');
            console.error('Submission error:', error);
        } finally {
            // Reset button state
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.innerHTML = '<i class="fas fa-paper-plane me-1"></i>Submit Code';
            }
        }
    }

    // Show output in the output panel
    showOutput(output, type = 'info') {
        const outputElement = document.getElementById('code-output');
        if (outputElement) {
            const alertClass = {
                'info': 'alert-info',
                'success': 'alert-success',
                'error': 'alert-danger',
                'warning': 'alert-warning'
            }[type] || 'alert-info';
            
            outputElement.innerHTML = `
                <div class="alert ${alertClass} mb-0">
                    <pre class="mb-0">${output}</pre>
                </div>
            `;
        }
    }

    // Clean up resources
    destroy() {
        if (this.autoSaveInterval) {
            clearInterval(this.autoSaveInterval);
        }
        if (this.editor) {
            this.editor.dispose();
        }
    }
}

// Global instance
window.codeEditor = new CodeEditorManager();

// Utility functions for quiz management
window.QuizUtils = {
    // Format time remaining
    formatTime: function(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        
        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        } else {
            return `${minutes}:${secs.toString().padStart(2, '0')}`;
        }
    },
    
    // Start quiz timer
    startTimer: function(timeLimit, onTimeUp) {
        let timeLeft = timeLimit * 60; // Convert minutes to seconds
        const timerElement = document.getElementById('quiz-timer');
        
        const countdown = setInterval(() => {
            timeLeft--;
            
            if (timerElement) {
                timerElement.textContent = this.formatTime(timeLeft);
                
                // Change color when time is running out
                if (timeLeft <= 300) { // 5 minutes
                    timerElement.className = 'text-warning fw-bold';
                } else if (timeLeft <= 60) { // 1 minute
                    timerElement.className = 'text-danger fw-bold';
                }
            }
            
            if (timeLeft <= 0) {
                clearInterval(countdown);
                if (onTimeUp) onTimeUp();
            }
        }, 1000);
        
        return countdown;
    }
};