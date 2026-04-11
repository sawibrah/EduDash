"""Shared helpers for course uploads, markdown slides, and templates."""
from datetime import datetime

UPLOAD_FOLDER = "static/uploads/slides"
ALLOWED_EXTENSIONS = {"pdf", "pptx"}
MAX_FILE_SIZE = 50 * 1024 * 1024


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_5_slide_template(title="", programming_language=""):
    """Generate a 5-slide markdown template for courses."""
    lang_lower = programming_language.lower() if programming_language else "programming"

    template = f"""# {title or "Course Title"}

---

## Slide 1: Introduction
### Welcome to {title or "Your Course"}

**Course Overview:**
- Learn {programming_language or "programming"} fundamentals
- Build practical projects
- Master key concepts step-by-step

**What You'll Achieve:**
- Write your first {lang_lower} program
- Understand core programming concepts
- Create real-world applications

```{lang_lower}
# Welcome! Let's start coding
print("Hello, {programming_language or "World"}!")
```

---

## Slide 2: Getting Started
### Setting Up Your Environment

**Prerequisites:**
- Basic computer skills
- Curiosity to learn
- No prior {lang_lower} experience needed

**Tools We'll Use:**
- Code editor (VS Code recommended)
- {programming_language or "Programming"} interpreter
- Project files and examples

**First Steps:**
1. Install the development environment
2. Write your first program
3. Run and test your code

```{lang_lower}
# Your first {lang_lower} program
def hello_world():
    return "Welcome to {programming_language or "programming"}!"
```

---

## Slide 3: Core Concepts
### Fundamental Building Blocks

**Key Topics Covered:**
- Variables and data types
- Functions and methods
- Control structures (if/else, loops)
- Data structures (lists, dictionaries)

**Hands-On Practice:**
- Interactive coding exercises
- Step-by-step examples
- Common patterns and best practices

```{lang_lower}
# Example: Working with variables
name = "Student"
age = 25
skills = ["{lang_lower}", "problem-solving", "creativity"]

print(f"{{name}} is {{age}} years old")
print(f"Skills: {{', '.join(skills)}}")
```

---

## Slide 4: Practical Projects
### Building Real Applications

**Project Examples:**
- Calculator application
- Data analysis tool
- Web scraper
- Game or interactive program

**Skills You'll Develop:**
- Problem-solving approach
- Code organization
- Testing and debugging
- Best practices

```{lang_lower}
# Example: Simple calculator
def calculator(num1, num2, operation):
    if operation == "+":
        return num1 + num2
    elif operation == "-":
        return num1 - num2
    else:
        return "Unknown operation"

# Usage
result = calculator(10, 5, "+")
print(f"Result: {{result}}")
```

---

## Slide 5: Next Steps
### Continue Your Learning Journey

**What You've Learned:**
- {programming_language or "Programming"} fundamentals
- Practical coding skills
- Problem-solving techniques
- Real project experience

**Continue Learning:**
- Practice with more projects
- Explore advanced topics
- Join coding communities
- Build your portfolio

**Resources:**
- Official {programming_language or "programming"} documentation
- Online coding platforms
- Open source projects
- Developer communities

```{lang_lower}
# Keep coding and learning!
print("Congratulations on completing the course!")
print("Your {lang_lower} journey has just begun!")
```

**Ready to take on new challenges? Keep coding!** 🚀"""

    return template


def convert_markdown_to_slides(markdown_content):
    """Convert markdown course content to Reveal.js slide sections."""
    import markdown

    if not markdown_content:
        return "<section><h1>No content available</h1></section>"

    lines = markdown_content.split("\n")
    slides = []
    current_slide = []

    for line in lines:
        if line.startswith("# "):
            if current_slide:
                slides.append("\n".join(current_slide))
                current_slide = []
            current_slide.append(line)
        elif line.startswith("## "):
            if current_slide:
                slides.append("\n".join(current_slide))
                current_slide = []
            current_slide.append(line)
        else:
            current_slide.append(line)

    if current_slide:
        slides.append("\n".join(current_slide))

    html_slides = []
    for slide_md in slides:
        if slide_md.strip():
            slide_html = markdown.markdown(slide_md, extensions=["codehilite", "fenced_code"])
            html_slides.append(f"<section>{slide_html}</section>")

    return "\n".join(html_slides) if html_slides else "<section><h1>No content available</h1></section>"
