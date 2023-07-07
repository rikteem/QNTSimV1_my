import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { environment } from 'src/environments/environment';
import { CookieService } from 'ngx-cookie-service';
import { tap } from 'rxjs';
import { Observable, Subject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiServiceService {
  private subject = new Subject<any>();
  public e2e: any
  public qsdc1: any
  public ghz: any
  ip1: any
  public pingpong: any
  constructor(private _http: HttpClient, private cookieService: CookieService) { }
  get getAccessToken() {
    return this.cookieService.get('access');
  }
  set setAccessToken(data: any) {
    this.cookieService.set('access', data);
  }
  get getRefreshToken() {
    return this.cookieService.get('refresh');
  }
  set setRefreshToken(data: any) {
    this.cookieService.set('refresh', data)
  }
  accessToken(data: any) {
    return this._http.post(environment.apiUrl + 'api/token/', data);
  }
  runApplication(data: any, apiUrl: string): Observable<any> {
    return this._http.post(apiUrl + 'run/', data)
  }
  advancedRunApplication(data: any, apiUrl: string): Observable<any> {
    const token = localStorage.getItem("access");
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);
    const observable = this._http.post(apiUrl + 'run/', data, { headers });

    // observable.subscribe(() => this.startStream(apiUrl));
    return observable;
  }

  async startStream(url: string) {
    const response = await fetch(`${url}/logs`);
    const reader = response.body.getReader();
    let text = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      text += new TextDecoder().decode(value);
      console.log(text)
      this.subject.next(text);
    }
  }

  getStream(): Observable<any> {
    return this.subject.asObservable();
  }
  ghz1() {
    return this.ghz
  }
  gete2e() {
    return this.e2e
  }
  getqsdc1() {
    return this.qsdc1;
  }
  getip1() {
    return this.ip1
  }
  getPingPong() {
    return this.pingpong
  }
  getCredentials() {
    return {
      "username": "admin",
      "password": "qwerty"
    }
  }
  getSavedModel() {
    return this._http.get('/assets/preload-topologies/advanced/savedModel.json');
  }
}
