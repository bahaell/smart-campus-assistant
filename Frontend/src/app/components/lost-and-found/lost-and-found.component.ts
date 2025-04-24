import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-lost-and-found',
  templateUrl: './lost-and-found.component.html',
  styleUrls: ['./lost-and-found.component.css']
})
export class LostAndFoundComponent implements OnInit {
  type: 'lost' | 'found' = 'lost';
  description: string = '';
  location: string = '';
  contactInfo: string = '';
  filter: 'all' | 'lost' | 'found' = 'all';
  items: any[] = [];
  filteredItems: any[] = [];
  selectedFile: File | null = null;
  private defaultApiUrl = '/api/lost-and-found'; // Valeur par défaut

  constructor(private http: HttpClient) {}

  // Propriété calculée pour obtenir l'URL dynamique via __env
  private get apiUrl(): string {
    return (window as any).__env?.lostAndFoundApiUrl || this.defaultApiUrl;
  }

  ngOnInit() {
    this.fetchItems();
  }

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.selectedFile = input.files[0];
    }
  }

  fetchItems() {
    this.http.get<any[]>(`${this.apiUrl}/items`).subscribe({
      next: (items) => {
        this.items = items.map(item => {
          return {
            ...item,
            expanded: false,
            image_path: item.image_path ? `${this.apiUrl}/${item.image_path}` : null
          };
        });
        this.applyFilter();
      },
      error: (error) => {
        console.error('Error fetching items:', error);
      }
    });
  }

  applyFilter() {
    if (this.filter === 'all') {
      this.filteredItems = this.items;
    } else {
      this.filteredItems = this.items.filter(item => item.type === this.filter);
    }
  }
  changeFilter(newFilter: 'all' | 'lost' | 'found') {
    this.filter = newFilter;
    this.applyFilter();
  }


  submitItem() {
    const formData = new FormData();
    formData.append('type', this.type);
    formData.append('description', this.description);
    if (this.location) formData.append('location', this.location);
    if (this.contactInfo) formData.append('contactInfo', this.contactInfo);
    if (this.selectedFile) formData.append('file', this.selectedFile, this.selectedFile.name);

    this.http.post(`${this.apiUrl}/upload`, formData).subscribe({
      next: () => {
        this.fetchItems();
        this.description = '';
        this.location = '';
        this.contactInfo = '';
        this.selectedFile = null;
        const fileInput = document.getElementById('image') as HTMLInputElement;
        if (fileInput) fileInput.value = '';
      },
      error: (error) => {
        console.error('Error submitting item:', error);
      }
    });
  }
}
