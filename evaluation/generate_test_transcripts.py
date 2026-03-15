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

# Profile 3: Spanish Economics Student - Realistic Economics Degree (ECTS) - RENUMBERED FROM 004
create_transcript_pdf(
    filename="PROFILE_003_ES_ECON_Transcript.pdf",
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

# Profile 4: German Business Informatics Student - Realistic Wirtschaftsinformatik Degree (ECTS)
create_transcript_pdf(
    filename="PROFILE_004_DE_BINF_Transcript.pdf",
    student_name="Lukas Müller",
    university="Hochschule München",
    courses=[
        # Mathematics \u0026 Foundations (Semesters 1-2)
        {"name": "Mathematics I", "credits": 6, "grade": "2.3"},
        {"name": "Mathematics II", "credits": 6, "grade": "2.0"},
        {"name": "Statistics", "credits": 6, "grade": "2.7"},
        {"name": "Linear Algebra", "credits": 6, "grade": "2.3"},
        
        # Computer Science Foundations (Semesters 1-3)
        {"name": "Introduction to Programming", "credits": 6, "grade": "1.7"},
        {"name": "Object-Oriented Programming", "credits": 6, "grade": "2.0"},
        {"name": "Data Structures and Algorithms", "credits": 6, "grade": "2.3"},
        {"name": "Database Systems", "credits": 6, "grade": "2.0"},
        {"name": "Software Engineering", "credits": 6, "grade": "2.3"},
        {"name": "Web Technologies", "credits": 6, "grade": "2.0"},
        
        # Business Foundations (Semesters 1-3)
        {"name": "Business Administration", "credits": 6, "grade": "2.3"},
        {"name": "Accounting", "credits": 6, "grade": "2.7"},
        {"name": "Marketing", "credits": 6, "grade": "2.3"},
        {"name": "Microeconomics", "credits": 6, "grade": "2.7"},
        {"name": "Macroeconomics", "credits": 6, "grade": "3.0"},
        
        # Business Informatics Core (Semesters 3-5)
        {"name": "Business Process Management", "credits": 6, "grade": "2.0"},
        {"name": "Enterprise Resource Planning (SAP)", "credits": 6, "grade": "2.3"},
        {"name": "IT Project Management", "credits": 6, "grade": "2.0"},
        {"name": "Business Intelligence", "credits": 6, "grade": "2.3"},
        {"name": "Data Analytics", "credits": 6, "grade": "2.0"},
        {"name": "IT Service Management", "credits": 6, "grade": "2.3"},
        {"name": "Enterprise Architecture", "credits": 6, "grade": "2.3"},
        
        # Advanced Topics (Semesters 5-6)
        {"name": "Digital Business Models", "credits": 6, "grade": "2.0"},
        {"name": "Cloud Computing", "credits": 6, "grade": "2.3"},
        {"name": "IT Security", "credits": 6, "grade": "2.7"},
        {"name": "Digital Transformation", "credits": 6, "grade": "2.0"},
        {"name": "IT Consulting", "credits": 6, "grade": "2.3"},
        
        # Electives (Semesters 6-7)
        {"name": "Machine Learning for Business", "credits": 6, "grade": "2.3"},
        {"name": "E-Commerce Systems", "credits": 6, "grade": "2.0"},
        {"name": "Business Law", "credits": 6, "grade": "2.7"},
        
        # Practical Experience (Semester 7)
        {"name": "Internship (Practical Semester)", "credits": 24, "grade": "2.0"},
        
        # Final Project (Semester 7)
        {"name": "Bachelor Thesis", "credits": 12, "grade": "2.3"},
    ],
    total_credits=210,
    semesters=7
)

# Profile 5: Pakistani Marketing Student - Realistic Marketing Degree
create_transcript_pdf(
    filename="PROFILE_005_PK_MKT_Transcript.pdf",
    student_name="Ayesha Khan",
    university="Lahore University of Management Sciences (LUMS)",
    courses=[
        # General Education (Semesters 1-2)
        {"name": "English Composition", "credits": 4, "grade": "A-"},
        {"name": "Business Communication", "credits": 4, "grade": "A"},
        {"name": "Islamic Studies", "credits": 3, "grade": "B+"},
        {"name": "Pakistan Studies", "credits": 3, "grade": "B+"},
        {"name": "Computer Applications", "credits": 4, "grade": "A"},
        
        # Business Foundations (Semesters 1-3)
        {"name": "Principles of Management", "credits": 4, "grade": "A-"},
        {"name": "Financial Accounting", "credits": 4, "grade": "B+"},
        {"name": "Managerial Accounting", "credits": 4, "grade": "B+"},
        {"name": "Business Mathematics", "credits": 4, "grade": "A-"},
        {"name": "Business Statistics", "credits": 4, "grade": "A"},
        {"name": "Microeconomics", "credits": 4, "grade": "B+"},
        {"name": "Macroeconomics", "credits": 4, "grade": "B+"},
        
        # Marketing Core (Semesters 2-5)
        {"name": "Principles of Marketing", "credits": 4, "grade": "A"},
        {"name": "Consumer Behavior", "credits": 4, "grade": "A"},
        {"name": "Marketing Research", "credits": 4, "grade": "A-"},
        {"name": "Brand Management", "credits": 4, "grade": "A"},
        {"name": "Strategic Marketing", "credits": 4, "grade": "A-"},
        {"name": "Marketing Analytics", "credits": 4, "grade": "A"},
        {"name": "Services Marketing", "credits": 4, "grade": "A-"},
        {"name": "International Marketing", "credits": 4, "grade": "B+"},
        
        # Digital Marketing Specialization (Semesters 4-6)
        {"name": "Digital Marketing", "credits": 4, "grade": "A"},
        {"name": "Social Media Marketing", "credits": 4, "grade": "A"},
        {"name": "Content Marketing", "credits": 4, "grade": "A"},
        {"name": "Search Engine Marketing", "credits": 4, "grade": "A-"},
        {"name": "E-Commerce", "credits": 4, "grade": "A-"},
        {"name": "Marketing Automation", "credits": 4, "grade": "A"},
        
        # Supporting Courses (Semesters 3-6)
        {"name": "Integrated Marketing Communications", "credits": 4, "grade": "A"},
        {"name": "Sales Management", "credits": 4, "grade": "B+"},
        {"name": "Retail Management", "credits": 4, "grade": "B+"},
        {"name": "Public Relations", "credits": 4, "grade": "A-"},
        {"name": "Advertising Management", "credits": 4, "grade": "A"},
        {"name": "Business Ethics", "credits": 3, "grade": "A-"},
        
        # Final Project (Semester 8)
        {"name": "Marketing Internship", "credits": 4, "grade": "A"},
        {"name": "Capstone Project", "credits": 4, "grade": "A"},
    ],
    total_credits=128,
    semesters=8
)

print("\n✅ All 5 transcript PDFs created successfully!")
print("\nFiles created:")
print("1. PROFILE_001_VN_CS_Transcript.pdf")
print("2. PROFILE_002_IN_BUS_Transcript.pdf")
print("3. PROFILE_003_ES_ECON_Transcript.pdf")
print("4. PROFILE_004_DE_BINF_Transcript.pdf")
print("5. PROFILE_005_PK_MKT_Transcript.pdf")
