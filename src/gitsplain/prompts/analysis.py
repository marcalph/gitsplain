"""Phase 1: gh analysis prompt."""

ANALYSIS_PROMPT = """
You are tasked with explaining to a principal software engineer how to draw the best and most accurate system design diagram / architecture of a given project. This explanation should be tailored to the specific project's purpose and structure. To accomplish this, you will be provided with the following information:

1. The complete and entire file tree of the project including all directory and file names, which will be enclosed in <filetree> tags in the users message.

2. The README file of the project, which will be enclosed in <readme> tags in the users message.


Analyze these components carefully, as they will provide crucial information about the project's structure and purpose. Follow these steps to create an explanation for the principal software engineer:

1. Identify the project type and purpose:
   - Examine the file structure and README to determine if the project is a full-stack application, an open-source framework, a compiler, or any other type of software imaginable.
   - Look for key indicators in the README, such as project description, features, or use cases.

2. Analyze the file structure:
   - Pay attention to top-level directories and their names (e.g., "frontend", "backend", "src", "lib", "tests").
   - Identify patterns in the directory structure that might indicate architectural choices (e.g., MVC pattern, microservices).
   - Note any configuration files, build scripts, or deployment-related files.

3. Analyze the extracted symbols:
   - Review the classes, modules, and structs extracted from the source code.
   - Identify key abstractions: services, models, controllers, handlers, etc.
   - Look for patterns in class names that indicate architectural roles (e.g., Service, Repository, Controller, Handler).
   - Use the symbols to understand the internal structure of each component.

4. Examine the README for additional insights:
   - Look for sections describing the architecture, dependencies, or technical stack.
   - Check for any diagrams or explanations of the system's components.

5. Based on your analysis, explain how to create a system design diagram that accurately represents the project's architecture. Include the following points:

   a. Identify the main components of the system (e.g., frontend, backend, database, building, external services).
   b. Determine the relationships and interactions between these components.
   c. Highlight any important architectural patterns or design principles used in the project.
   d. Include relevant technologies, frameworks, or libraries that play a significant role in the system's architecture.
   e. Reference specific classes/modules from the symbols to justify component boundaries.

6. Provide guidelines for tailoring the diagram to the specific project type:
   - For a full-stack application, emphasize the separation between frontend and backend, database interactions, and any API layers.
   - For an open-source tool, focus on the core functionality, extensibility points, and how it integrates with other systems.
   - For a compiler or language-related project, highlight the different stages of compilation or interpretation, and any intermediate representations.

7. Instruct the principal software engineer to include the following elements in the diagram:
   - Clear labels for each component
   - Directional arrows to show data flow or dependencies
   - Color coding or shapes to distinguish between different types of components

8. NOTE: Emphasize the importance of being very detailed and capturing the essential architectural elements. Use the extracted symbols to ensure accuracy - class and module names should inform component naming.

Present your explanation and instructions within <explanation> tags, ensuring that you tailor your advice to the specific project based on the provided filetree and README content.
"""
