import { Component } from '@angular/core';
import { Router } from '@angular/router';

@Component({
  selector: 'app-services',
  templateUrl: './services.component.html',
  styleUrls: ['./services.component.css']
})
export class ServicesComponent {
  services = [
    {
      title: 'Campus Assistant',
      description: 'Get instant answers to your questions about campus facilities, events, and locations.',
      icon: 'bot',
      route: '/',
      bgColor: 'bg-blue-500',
      hoverColor: 'hover:bg-blue-600',
      Access : 'Access'
    },
    {
      title: 'Lost & Found',
      description: 'Report lost items or items you\'ve found to help reunite people with their belongings.',
      icon: 'search',
      route: '/lost-and-found',
      bgColor: 'bg-indigo-500',
      hoverColor: 'hover:bg-indigo-600',
      Access : 'Access'
    },
    {
      title: 'Campus Map',
      description: 'Interactive map with real-time navigation to help you find your way around campus.',
      icon: 'map-pin',
      route: '/coming-soon',
      bgColor: 'bg-teal-500',
      hoverColor: 'hover:bg-teal-600',
      Access : 'Coming Soon'
    },
    {
      title: 'Event Calendar',
      description: 'Stay updated with all campus events, activities, and important dates.',
      icon: 'calendar',
      route: '/coming-soon',
      bgColor: 'bg-purple-500',
      hoverColor: 'hover:bg-purple-600',
      Access : 'Coming Soon'
    }
  ];

  constructor(private router: Router) {}

  navigateTo(route: string): void {
    this.router.navigate([route]);
  }
}
