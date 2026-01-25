"""
Generate 5 PDF transcript files for test profiles
Each PDF contains course names and credit points in a table format
"""

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle

def create_transcript_pdf(filename, student_name, university, courses, total_credits, semesters):
    """
    Create a PDF transcript with course names and credits
    
    Args:
        filename: Output PDF filename
        student_name: Student's full name
        university: University name
        courses: List of dicts with 'name' and 'credits' keys
        total_credits: Total credits earned
        semesters: Number of semesters
    """
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "OFFICIAL TRANSCRIPT OF RECORDS")
    
    # Student Info
    c.setFont("Helvetica", 12)
    y = height - 100
    c.drawString(50, y, f"Student Name: {student_name}")
    y -= 20
    c.drawString(50, y, f"University: {university}")
    y -= 20
    c.drawString(50, y, f"Program Duration: {semesters} semesters")
    y -= 20
    c.drawString(50, y, f"Total Credits Earned: {total_credits}")
    
    # Course Table
    y -= 40
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Courses Completed:")
    
    y -= 30
    
    # Table header
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Course Name")
    c.drawString(400, y, "Credits")
    c.drawString(480, y, "Grade")
    
    y -= 5
    c.line(50, y, width - 50, y)  # Horizontal line
    
    # Course rows
    c.setFont("Helvetica", 10)
    y -= 20
    
    for course in courses:
        if y < 100:  # New page if needed
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 10)
        
        course_name = course['name']
        credits = str(course['credits'])
        grade = course.get('grade', 'A')  # Default grade
        
        c.drawString(50, y, course_name)
        c.drawString(400, y, credits)
        c.drawString(480, y, grade)
        y -= 20
    
    # Footer
    y -= 20
    c.line(50, y, width - 50, y)
    y -= 20
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, f"TOTAL CREDITS: {total_credits}")
    
    y -= 40
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(50, y, "This is an official transcript. Issued on: 2024-12-15")
    
    c.save()
    print(f"✅ Created: {filename}")


# Profile 1: Vietnamese CS Student - Realistic Bachelor's Degree
create_transcript_pdf(
    filename="PROFILE_001_VN_CS_Transcript.pdf",
    student_name="Linh Nguyen",
    university="Hanoi University of Science and Technology",
    courses=[
        # General Education (Semesters 1-2)
        {"name": "English I", "credits": 2, "grade": "B+"},
        {"name": "English II", "credits": 2, "grade": "A-"},
        {"name": "Vietnamese Literature", "credits": 2, "grade": "B"},
        {"name": "Philosophy", "credits": 2, "grade": "B+"},
        {"name": "Political Science", "credits": 2, "grade": "B"},
        {"name": "Physical Education I", "credits": 1, "grade": "A"},
        {"name": "Physical Education II", "credits": 1, "grade": "A"},
        
        # Mathematics Foundation (Semesters 1-3)
        {"name": "Calculus I", "credits": 4, "grade": "A"},
        {"name": "Calculus II", "credits": 4, "grade": "A"},
        {"name": "Linear Algebra", "credits": 3, "grade": "A-"},
        {"name": "Discrete Mathematics", "credits": 3, "grade": "A"},
        {"name": "Probability and Statistics", "credits": 3, "grade": "A"},
        
        # Physics & Science (Semesters 1-2)
        {"name": "Physics I", "credits": 3, "grade": "B+"},
        {"name": "Physics II", "credits": 3, "grade": "B+"},
        
        # CS Core Courses (Semesters 2-6)
        {"name": "Introduction to Programming", "credits": 4, "grade": "A"},
        {"name": "Object-Oriented Programming", "credits": 4, "grade": "A"},
        {"name": "Data Structures", "credits": 4, "grade": "A"},
        {"name": "Algorithms", "credits": 4, "grade": "A"},
        {"name": "Computer Architecture", "credits": 3, "grade": "B+"},
        {"name": "Operating Systems", "credits": 4, "grade": "A-"},
        {"name": "Database Systems", "credits": 3, "grade": "A"},
        {"name": "Computer Networks", "credits": 3, "grade": "B+"},
        {"name": "Software Engineering", "credits": 4, "grade": "A"},
        {"name": "Theory of Computation", "credits": 3, "grade": "A-"},
        
        # Advanced CS (Semesters 5-7)
        {"name": "Machine Learning", "credits": 3, "grade": "A"},
        {"name": "Artificial Intelligence", "credits": 3, "grade": "A"},
        {"name": "Web Development", "credits": 3, "grade": "A-"},
        {"name": "Mobile App Development", "credits": 3, "grade": "B+"},
        {"name": "Computer Graphics", "credits": 3, "grade": "A-"},
        {"name": "Compiler Design", "credits": 3, "grade": "B+"},
        
        # Electives (Semesters 6-7)
        {"name": "Digital Marketing", "credits": 2, "grade": "B+"},
        {"name": "Entrepreneurship", "credits": 2, "grade": "A-"},
        
        # Final Project (Semester 8)
        {"name": "Capstone Project", "credits": 4, "grade": "A"},
        {"name": "Internship", "credits": 3, "grade": "A"},
    ],
    total_credits=130,
    semesters=8
)

# Profile 2: Indian Business Student - Realistic BBA Degree
create_transcript_pdf(
    filename="PROFILE_002_IN_BUS_Transcript.pdf",
    student_name="Raj Patel",
    university="Delhi University",
    courses=[
        # General Education (Semesters 1-2)
        {"name": "English Communication", "credits": 4, "grade": "A"},
        {"name": "Business Mathematics", "credits": 6, "grade": "A-"},
        {"name": "Environmental Studies", "credits": 4, "grade": "B+"},
        {"name": "Indian Constitution", "credits": 4, "grade": "B+"},
        {"name": "Computer Fundamentals", "credits": 4, "grade": "A"},
        
        # Business Foundation (Semesters 1-3)
        {"name": "Principles of Management", "credits": 6, "grade": "A"},
        {"name": "Financial Accounting", "credits": 6, "grade": "A"},
        {"name": "Managerial Economics", "credits": 6, "grade": "A-"},
        {"name": "Business Statistics", "credits": 6, "grade": "A"},
        {"name": "Business Law", "credits": 6, "grade": "B+"},
        
        # Core Business Courses (Semesters 3-5)
        {"name": "Marketing Management", "credits": 6, "grade": "A"},
        {"name": "Human Resource Management", "credits": 6, "grade": "A-"},
        {"name": "Operations Management", "credits": 6, "grade": "A"},
        {"name": "Financial Management", "credits": 6, "grade": "A"},
        {"name": "Organizational Behavior", "credits": 6, "grade": "A-"},
        {"name": "Strategic Management", "credits": 6, "grade": "A"},
        {"name": "Corporate Finance", "credits": 6, "grade": "A"},
        {"name": "Business Communication", "credits": 4, "grade": "A"},
        
        # Specialization: Analytics & Digital (Semesters 4-6)
        {"name": "Business Analytics", "credits": 6, "grade": "A"},
        {"name": "Digital Marketing", "credits": 6, "grade": "A"},
        {"name": "Supply Chain Management", "credits": 6, "grade": "A-"},
        {"name": "Innovation Management", "credits": 6, "grade": "A"},
        {"name": "E-Commerce", "credits": 6, "grade": "A"},
        {"name": "Consumer Behavior", "credits": 6, "grade": "A-"},
        
        # Electives (Semesters 5-6)
        {"name": "International Business", "credits": 6, "grade": "A"},
        {"name": "Entrepreneurship", "credits": 6, "grade": "A"},
        {"name": "Project Management", "credits": 6, "grade": "A"},
        {"name": "Business Ethics", "credits": 4, "grade": "A-"},
        
        # Final Project (Semester 6)
        {"name": "Internship", "credits": 8, "grade": "A"},
        {"name": "Capstone Project", "credits": 6, "grade": "A"},
    ],
    total_credits=180,
    semesters=6
)

# Profile 3: Chinese Engineering Student - Realistic Mechanical Engineering Degree
create_transcript_pdf(
    filename="PROFILE_003_CN_ENG_Transcript.pdf",
    student_name="Wei Zhang",
    university="Tsinghua University",
    courses=[
        # General Education (Semesters 1-2)
        {"name": "English I", "credits": 3, "grade": "A"},
        {"name": "English II", "credits": 3, "grade": "A"},
        {"name": "Chinese Literature", "credits": 2, "grade": "A-"},
        {"name": "Marxist Philosophy", "credits": 3, "grade": "A"},
        {"name": "Modern Chinese History", "credits": 2, "grade": "A-"},
        {"name": "Physical Education I", "credits": 1, "grade": "A"},
        {"name": "Physical Education II", "credits": 1, "grade": "A"},
        
        # Mathematics & Science Foundation (Semesters 1-3)
        {"name": "Engineering Mathematics I", "credits": 5, "grade": "A"},
        {"name": "Engineering Mathematics II", "credits": 5, "grade": "A"},
        {"name": "Physics for Engineers I", "credits": 4, "grade": "A"},
        {"name": "Physics for Engineers II", "credits": 4, "grade": "A"},
        {"name": "Chemistry for Engineers", "credits": 3, "grade": "A-"},
        
        # Engineering Foundation (Semesters 2-4)
        {"name": "Engineering Drawing", "credits": 3, "grade": "A"},
        {"name": "Engineering Mechanics", "credits": 4, "grade": "A"},
        {"name": "Materials Science", "credits": 3, "grade": "A"},
        {"name": "Thermodynamics", "credits": 4, "grade": "A"},
        {"name": "Fluid Mechanics", "credits": 4, "grade": "A"},
        {"name": "Electrical Engineering Basics", "credits": 3, "grade": "A-"},
        
        # Mechanical Engineering Core (Semesters 3-6)
        {"name": "Machine Design", "credits": 4, "grade": "A"},
        {"name": "Manufacturing Processes", "credits": 4, "grade": "A"},
        {"name": "Heat Transfer", "credits": 3, "grade": "A"},
        {"name": "Dynamics of Machinery", "credits": 3, "grade": "A"},
        {"name": "Control Systems", "credits": 4, "grade": "A"},
        {"name": "CAD/CAM", "credits": 3, "grade": "A"},
        {"name": "Finite Element Analysis", "credits": 3, "grade": "A"},
        {"name": "Vibration Analysis", "credits": 3, "grade": "A"},
        
        # Specialization: Automotive & Robotics (Semesters 5-7)
        {"name": "Automotive Engineering", "credits": 4, "grade": "A"},
        {"name": "Robotics", "credits": 3, "grade": "A"},
        {"name": "Mechatronics", "credits": 4, "grade": "A"},
        {"name": "Industrial Automation", "credits": 3, "grade": "A"},
        {"name": "Vehicle Dynamics", "credits": 3, "grade": "A"},
        
        # Electives (Semesters 6-7)
        {"name": "Quality Engineering", "credits": 3, "grade": "A-"},
        {"name": "Engineering Economics", "credits": 3, "grade": "A"},
        {"name": "Project Management", "credits": 3, "grade": "A"},
        
        # Final Project (Semester 8)
        {"name": "Internship", "credits": 4, "grade": "A"},
        {"name": "Capstone Design Project", "credits": 5, "grade": "A"},
    ],
    total_credits=140,
    semesters=8
)

# Profile 4: Spanish Economics Student - Realistic Economics Degree (ECTS)
create_transcript_pdf(
    filename="PROFILE_004_ES_ECON_Transcript.pdf",
    student_name="Maria Garcia",
    university="Universidad Complutense de Madrid",
    courses=[
        # General Education (Year 1)
        {"name": "Spanish Language and Literature", "credits": 6, "grade": "6.5"},
        {"name": "English for Academic Purposes", "credits": 6, "grade": "7.0"},
        {"name": "Introduction to Philosophy", "credits": 6, "grade": "6.3"},
        {"name": "History of Economic Thought", "credits": 6, "grade": "6.5"},
        {"name": "Computer Skills", "credits": 6, "grade": "6.8"},
        
        # Mathematics & Statistics Foundation (Years 1-2)
        {"name": "Mathematics for Economists I", "credits": 6, "grade": "6.5"},
        {"name": "Mathematics for Economists II", "credits": 6, "grade": "6.4"},
        {"name": "Economic Statistics", "credits": 6, "grade": "6.8"},
        {"name": "Econometrics", "credits": 6, "grade": "7.5"},
        
        # Economics Core (Years 1-3)
        {"name": "Principles of Economics", "credits": 6, "grade": "6.7"},
        {"name": "Microeconomics I", "credits": 6, "grade": "7.0"},
        {"name": "Microeconomics II", "credits": 6, "grade": "6.8"},
        {"name": "Macroeconomics I", "credits": 6, "grade": "6.5"},
        {"name": "Macroeconomics II", "credits": 6, "grade": "6.6"},
        {"name": "Economic History", "credits": 6, "grade": "6.2"},
        {"name": "Spanish Economy", "credits": 6, "grade": "6.7"},
        {"name": "European Economy", "credits": 6, "grade": "6.8"},
        
        # Finance & Business (Years 2-3)
        {"name": "Accounting Principles", "credits": 6, "grade": "6.6"},
        {"name": "Financial Markets", "credits": 6, "grade": "7.0"},
        {"name": "Corporate Finance", "credits": 6, "grade": "6.9"},
        {"name": "Banking and Finance", "credits": 6, "grade": "6.8"},
        {"name": "Investment Analysis", "credits": 6, "grade": "6.5"},
        
        # Public Economics & Policy (Years 2-3)
        {"name": "Public Finance", "credits": 6, "grade": "6.5"},
        {"name": "Public Economics", "credits": 6, "grade": "6.4"},
        {"name": "Economic Policy", "credits": 6, "grade": "6.6"},
        {"name": "Fiscal Policy", "credits": 6, "grade": "6.7"},
        
        # International & Development (Years 3-4)
        {"name": "International Economics", "credits": 6, "grade": "6.8"},
        {"name": "International Trade", "credits": 6, "grade": "6.9"},
        {"name": "Development Economics", "credits": 6, "grade": "6.8"},
        {"name": "Economic Integration", "credits": 6, "grade": "6.7"},
        {"name": "Globalization and Economy", "credits": 6, "grade": "6.6"},
        
        # Specialized Economics (Years 3-4)
        {"name": "Labor Economics", "credits": 6, "grade": "6.7"},
        {"name": "Industrial Organization", "credits": 6, "grade": "6.4"},
        {"name": "Environmental Economics", "credits": 6, "grade": "6.8"},
        {"name": "Sustainable Development", "credits": 6, "grade": "7.0"},
        {"name": "Behavioral Economics", "credits": 6, "grade": "7.0"},
        {"name": "Economic Growth", "credits": 6, "grade": "6.7"},
        
        # Electives (Year 4)
        {"name": "Game Theory", "credits": 6, "grade": "7.2"},
        {"name": "Research Methods", "credits": 6, "grade": "6.6"},
        {"name": "Risk Management", "credits": 6, "grade": "6.6"},
        
        # Final Project (Year 4)
        {"name": "Bachelor Thesis", "credits": 12, "grade": "7.2"},
    ],
    total_credits=240,
    semesters=8
)

# Profile 5: US Liberal Arts Student - Realistic Interdisciplinary Degree
create_transcript_pdf(
    filename="PROFILE_005_US_LIBERAL_Transcript.pdf",
    student_name="Alex Johnson",
    university="US University (Liberal Arts)",
    courses=[
        # General Education Requirements (Years 1-2)
        {"name": "English Composition I", "credits": 3, "grade": "A"},
        {"name": "English Composition II", "credits": 3, "grade": "A-"},
        {"name": "Public Speaking", "credits": 3, "grade": "A"},
        {"name": "World History", "credits": 3, "grade": "A-"},
        {"name": "Introduction to Sociology", "credits": 3, "grade": "A"},
        {"name": "Introduction to Philosophy", "credits": 3, "grade": "A-"},
        {"name": "Art Appreciation", "credits": 3, "grade": "A"},
        {"name": "Physical Education", "credits": 2, "grade": "A"},
        
        # Psychology Major Courses (Years 1-4)
        {"name": "Introduction to Psychology", "credits": 3, "grade": "A"},
        {"name": "Cognitive Psychology", "credits": 3, "grade": "A"},
        {"name": "Social Psychology", "credits": 3, "grade": "A"},
        {"name": "Developmental Psychology", "credits": 3, "grade": "A-"},
        {"name": "Abnormal Psychology", "credits": 3, "grade": "B+"},
        {"name": "Neuroscience", "credits": 3, "grade": "A"},
        {"name": "Experimental Psychology", "credits": 3, "grade": "A-"},
        {"name": "Perception and Cognition", "credits": 3, "grade": "A"},
        {"name": "Learning and Memory", "credits": 3, "grade": "A"},
        {"name": "Psychology of Technology", "credits": 3, "grade": "A"},
        {"name": "Human Factors", "credits": 3, "grade": "A-"},
        {"name": "Cognitive Science", "credits": 3, "grade": "A"},
        
        # Statistics Minor (Years 2-3)
        {"name": "Statistics I", "credits": 3, "grade": "A"},
        {"name": "Statistics II", "credits": 3, "grade": "A"},
        {"name": "Behavioral Statistics", "credits": 3, "grade": "A"},
        {"name": "Applied Statistics", "credits": 3, "grade": "A"},
        {"name": "Data Analysis", "credits": 3, "grade": "A"},
        {"name": "Quantitative Methods", "credits": 3, "grade": "A"},
        {"name": "Regression Analysis", "credits": 3, "grade": "A-"},
        {"name": "Data Visualization", "credits": 3, "grade": "A"},
        
        # Computer Science Electives (Years 2-4)
        {"name": "Introduction to Computer Science", "credits": 3, "grade": "A"},
        {"name": "Programming in Python", "credits": 3, "grade": "A-"},
        {"name": "Database Fundamentals", "credits": 3, "grade": "B+"},
        {"name": "Web Technologies", "credits": 3, "grade": "A"},
        {"name": "Machine Learning Basics", "credits": 3, "grade": "A-"},
        
        # HCI/UX Specialization (Years 3-4)
        {"name": "Human-Computer Interaction", "credits": 3, "grade": "A"},
        {"name": "User Experience Design", "credits": 3, "grade": "A"},
        {"name": "Information Architecture", "credits": 3, "grade": "A"},
        {"name": "Usability Testing", "credits": 3, "grade": "A-"},
        {"name": "Interaction Design", "credits": 3, "grade": "A"},
        {"name": "Visual Design", "credits": 3, "grade": "A-"},
        
        # Research Methods (Years 3-4)
        {"name": "Research Methods in Psychology", "credits": 3, "grade": "A-"},
        {"name": "Research Design", "credits": 3, "grade": "A-"},
        {"name": "Survey Methods", "credits": 3, "grade": "A"},
        {"name": "Qualitative Research", "credits": 3, "grade": "A"},
        {"name": "Ethics in Research", "credits": 3, "grade": "A"},
        
        # Final Year (Year 4)
        {"name": "Senior Thesis", "credits": 6, "grade": "A"},
        {"name": "Internship", "credits": 3, "grade": "A"},
        {"name": "Capstone Project", "credits": 3, "grade": "A"},
    ],
    total_credits=120,
    semesters=8
)

print("\n✅ All 5 transcript PDFs created successfully!")
print("\nFiles created:")
print("1. PROFILE_001_VN_CS_Transcript.pdf")
print("2. PROFILE_002_IN_BUS_Transcript.pdf")
print("3. PROFILE_003_CN_ENG_Transcript.pdf")
print("4. PROFILE_004_ES_ECON_Transcript.pdf")
print("5. PROFILE_005_US_LIBERAL_Transcript.pdf")
