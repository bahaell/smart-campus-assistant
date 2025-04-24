import { Component } from '@angular/core';

@Component({
  selector: 'app-about',
  templateUrl: './about.component.html',
  styleUrls: ['./about.component.css']
})
export class AboutComponent {
  teamMembers = [
    {
      name: 'BahaEddine Ellouze',
      role: 'Project Lead',
      bio: 'Software Engineering Student'
    }
  ];

  features = [
    { name: 'AI-Powered Assistance', description: 'Natural language processing to answer campus questions' },
    { name: 'Interactive Maps', description: 'Real-time navigation and location services' },
    { name: 'Lost & Found System', description: 'Digital platform to report and recover lost items' },
    { name: 'Event Management', description: 'Comprehensive calendar of campus activities' },
    { name: 'Mobile Friendly', description: 'Access services from any device, anywhere' },
    { name: 'Privacy Focused', description: 'Secure handling of all user information' }
  ];

}
