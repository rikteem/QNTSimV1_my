import { AfterViewInit, Component, OnInit } from '@angular/core';
import * as D3 from 'd3';
import Globe from 'globe.gl';
import { ConditionsService } from 'src/services/conditions.service';
import * as _ from 'underscore';

@Component({
  selector: 'app-home-page',
  templateUrl: './home-page.component.html',
  styleUrls: ['./home-page.component.less']
})
export class HomePageComponent implements OnInit, AfterViewInit {
  constructor(private conService: ConditionsService) { }
  ngOnInit(): void {
    this.conService.currentSection = 'home'
  }
  ngAfterViewInit(): void {
    var globe = <HTMLElement>document.getElementById('globe');
    console.log("col-5" + globe.clientHeight)
    const parallax = document.getElementById("parallax")!;
    // Parallax Effect for DIV 1
    window.addEventListener("scroll", function () {
      let offset = window.pageYOffset;
      parallax.style.backgroundPositionY = offset * 0.4 + "px";
      // DIV 1 background will move slower than other elements on scroll.
    })


    const COUNTRY = 'India';
    const OPACITY = 0.5;
    const myGlobe = Globe()
      (<HTMLElement>document.getElementById('globeViz'))
      .globeImageUrl('//unpkg.com/three-globe/example/img/earth-blue-marble.jpg')
      .pointOfView({
        lat: 28.7041,
        lng: 77.1025,
        altitude: 2
      }) // aim at continental US centroid
      .height(globe.clientHeight / 1.5)
      .width(globe.clientWidth)
      .backgroundColor('rgba(0,0,0,0)')
      // .arcLabel((d: any) => `${d.airline}: ${d.srcIata} &#8594; ${d.dstIata}`)
      .arcStartLat((d: any) => +d.srcAirport.lat)
      .arcStartLng((d: any) => +d.srcAirport.lng)
      .arcEndLat((d: any) => +d.dstAirport.lat)
      .arcEndLng((d: any) => +d.dstAirport.lng)
      .arcDashLength(1)
      .arcDashGap(1)
      .arcDashInitialGap(() => Math.random())
      .arcDashAnimateTime(4000)
      .arcColor((d: any) => [`rgba(255, 255,255, ${OPACITY})`, `rgba(3, 207, 252, ${OPACITY})`])
      .arcsTransitionDuration(0)
      .pointColor(() => 'orange')
      .pointAltitude(0)
      .pointRadius(0.2)
      .pointsMerge(true);
    // myGlobe.position.y = 1000;
    // load data
    const airportParse = ([airportId, name, city, country, iata, icao, lat, lng, alt, timezone, dst, tz, type, source]: any) => ({
      airportId,
      name,
      city,
      country,
      iata,
      icao,
      lat,
      lng,
      alt,
      timezone,
      dst,
      tz,
      type,
      source
    });
    const routeParse = ([airline, airlineId, srcIata, srcAirportId, dstIata, dstAirportId, codeshare, stops, equipment]: any) => ({
      airline,
      airlineId,
      srcIata,
      srcAirportId,
      dstIata,
      dstAirportId,
      codeshare,
      stops,
      equipment
    });



    Promise.all([
      fetch('https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat').then(res => res.text())
        .then(d => D3.csvParseRows(d, airportParse)),
      fetch('https://raw.githubusercontent.com/jpatokal/openflights/master/data/routes.dat').then(res => res.text())
        .then(d => D3.csvParseRows(d, routeParse)),
      fetch('https://globe.gl/example/datasets/ne_110m_admin_0_countries.geojson').then(res => res.json())
        .then(countries => countries.features)
    ]).then(([airports, routes, cuntData]) => {
      const byIata = _.indexBy(airports, 'iata', false);
      const filteredRoutes = routes
        .filter((d: any) => byIata.hasOwnProperty(d.srcIata) && byIata.hasOwnProperty(d.dstIata)) // exclude unknown airports
        .filter((d: any) => d.stops === '0') // non-stop flights only
        .map((d: any) => Object.assign(d, {
          srcAirport: byIata[d.srcIata],
          dstAirport: byIata[d.dstIata]
        }))
        .filter((d: any) => d.srcAirport.country === COUNTRY && d.dstAirport.country !== COUNTRY); // international routes from country

      // const gData = [...Array(N).keys()].map(() => ({
      //   lat: (Math.random() - 0.5) * 180,
      //   lng: (Math.random() - 0.5) * 360,
      //   size: 7 + Math.random() * 30,
      //   color: ['red', 'white', 'blue', 'green'][Math.round(Math.random() * 3)]
      // }));
      [{
        lat: 17.385,
        lng: 78.4867,
      }];

      myGlobe.controls().autoRotate = true;
      // myGlobe.position.y = -1000
      myGlobe
        .polygonsData(cuntData)
        .polygonCapColor((feat: any) => feat.properties.NAME == COUNTRY ? "#6B7B8C" : "#6B7B8C")
        .polygonSideColor(() => 'rgba(0, 100, 0, 0.15)')
        .polygonStrokeColor(() => '#55626f')
        // .htmlElementsData(gData)
        // .htmlElement((d: any) => {
        //   const el = document.createElement('div');
        //   el.innerHTML = `<svg viewBox="-4 0 36 36">
        //       <path fill="currentColor" d="M14,0 C21.732,0 28,5.641 28,12.6 C28,23.963 14,36 14,36 C14,36 0,24.064 0,12.6 C0,5.641 6.268,0 14,0 Z"></path>
        //       <circle fill="black" cx="14" cy="14" r="7"></circle>
        //     </svg>`;
        //   el.style.color = 'red';
        //   el.style.width = '2px';

        //   el.style['pointer-events'] = 'auto';
        //   el.style.cursor = 'pointer';

        //   el.style['pointer-events'] = 'auto';
        //   el.style.cursor = 'pointer';
        //   el.onclick = () => console.info(d);
        //   return el;
        // })
        // .pointsData(airports)
        .arcsData(filteredRoutes);
    });
  }
}
