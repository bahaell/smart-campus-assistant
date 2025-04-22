Frontend





Purpose: Web interface for interacting with the Navigation Bot and Lost-and-Found Assistant.



Tech Stack: Angular, Tailwind CSS, Lucide icons, HttpClient.



Key Files:





app-routing.module.ts: Defines routes for Navigation Bot (/) and Lost-and-Found (/lost-and-found).



app.component.html: Root component with tabbed navigation and footer.



navigation-bot.component.ts/html: Chat interface with gradient header, message list, and typing indicator.



lost-and-found.component.ts/html: Form for submitting items and grid of item cards with matches.



footer.component.ts/html: Dark footer with links.



Styling:





Uses Tailwind CSS with a blue/indigo gradient for headers, white cards with shadows, and blue/teal buttons.



Matches the design of the React frontend with responsive layouts and Lucide icons.



Dependencies:





Tailwind CSS for styling.



Lucide Angular for icons (Send, MapPin, User, Calendar, ChevronDown, ChevronUp).



Angular HttpClient for API calls.



Angular Forms for form handling.



Running Locally:





Run ng serve for development (http://localhost:4200).



Use docker-compose up -d frontend for production (http://localhost:80).

Code Documentation

Lost-and-Found Assistant





Purpose: Matches lost and found items using image and text recognition.



Tech Stack: Python, FastAPI, YOLOv5, SentenceTransformers, MongoDB.



Key Files:





image_recognition.py: Detects objects in images using YOLOv5.



text_matching.py: Computes similarity between item descriptions using SentenceTransformers.



main.py: FastAPI application with /upload and /match endpoints.



Endpoints:





POST /upload: Uploads an item (image + description) and stores it in MongoDB.



POST /match: Finds similar items based on description, using a similarity threshold of 0.7.



Dependencies:





YOLOv5 model (yolov5s.pt) must be placed in the service directory.



MongoDB service must be running (via docker-compose).