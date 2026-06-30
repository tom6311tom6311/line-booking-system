import { Facebook, MapPin, Phone } from "lucide-react";
import { Header } from "./components/Header";
import { RoomCard } from "./components/RoomCard";
import { SectionHeading } from "./components/SectionHeading";
import { nearbyPlaces } from "./data/nearby";
import { rooms } from "./data/rooms";
import { services } from "./data/services";
import heroImage from "./assets/images/hero.jpg";
import mapImage from "./assets/images/map.jpg";
import propertyView from "./assets/images/property-view.jpg";

export function App() {
  return (
    <>
      <Header />
      <main id="top">
        <section className="hero" aria-label="富莉庭緣民宿">
          <img className="hero-image" src={heroImage} alt="埔里富莉庭緣民宿外觀與庭院" />
          <div className="hero-overlay" />
          <div className="hero-content">
            <p className="eyebrow">南投埔里・合法民宿 658 號</p>
            <h1>埔里富莉庭緣民宿</h1>
            <p>
              在山景、菜園與鄉間小路之間住一晚。適合家庭旅行、朋友包棟與想慢下來的埔里行程。
            </p>
            <div className="hero-actions">
              <a className="primary-button" href="tel:0932929748">
                <Phone size={19} aria-hidden="true" />
                電話訂房
              </a>
              <a className="secondary-button" href="#rooms">
                查看房型
              </a>
            </div>
          </div>
        </section>

        <section className="intro-section">
          <div className="intro-copy">
            <p className="eyebrow">About Fully BnB</p>
            <h2>離埔里市區不遠，也離日常喧鬧遠一點。</h2>
            <p>
              富莉庭緣位在埔里東埔，四周有山、有田、有村落。這裡不是大型飯店，而是一間重視自在、好客與在地生活感的民宿。
            </p>
          </div>
          <img src={propertyView} alt="富莉庭緣民宿庭院與建築景觀" />
        </section>

        <section className="section" id="rooms">
          <SectionHeading eyebrow="Rooms" title="房型與價格">
            雙人景觀套房、四人家庭房與 10 至 24 人包棟方案。房價含早餐，春節價格另計。
          </SectionHeading>
          <div className="room-grid">
            {rooms.map((room) => (
              <RoomCard key={room.name} room={room} />
            ))}
          </div>
          <div className="booking-note">
            <strong>包棟方案 NT$15,000 起。</strong>
            <span>目前以電話預約為主，也可透過 Booking.com 查詢房況。</span>
          </div>
        </section>

        <section className="section band" id="services">
          <SectionHeading eyebrow="Services" title="住宿服務">
            把常被詢問的資訊集中呈現，讓旅客更快判斷是否適合這趟旅行。
          </SectionHeading>
          <div className="service-grid">
            {services.map(({ title, description, Icon }) => (
              <article className="service-card" key={title}>
                <Icon size={24} aria-hidden="true" />
                <h3>{title}</h3>
                <p>{description}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="section" id="nearby">
          <SectionHeading eyebrow="Nearby" title="附近可以這樣玩">
            先放入精選景點，後續可再擴充成完整的埔里在地指南。
          </SectionHeading>
          <div className="nearby-grid">
            {nearbyPlaces.map((place) => (
              <article className="nearby-card" key={place.name}>
                <img src={place.image} alt={place.name} />
                <div>
                  <p className="eyebrow">{place.category}</p>
                  <h3>{place.name}</h3>
                  <p>{place.description}</p>
                  <span>{place.distance}</span>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="section traffic-section" id="traffic">
          <div>
            <SectionHeading eyebrow="Traffic" title="交通與位置">
              導航可搜尋「富莉庭緣民宿」。自行開車由國道六號埔里交流道下，往武界路、麒麟橋方向前往。
            </SectionHeading>
            <div className="contact-list">
              <a href="tel:0932929748">
                <Phone size={19} aria-hidden="true" />
                0932-929748 黃先生
              </a>
              <a href="https://www.facebook.com/fullybnb/?ref=bookmarks">
                <Facebook size={19} aria-hidden="true" />
                Facebook 粉絲團
              </a>
              <p>
                <MapPin size={19} aria-hidden="true" />
                南投縣埔里鎮麒麟里武界路 38 號
              </p>
            </div>
          </div>
          <img src={mapImage} alt="富莉庭緣民宿簡易地圖" />
        </section>
      </main>
      <footer className="site-footer">
        <p>富莉庭緣民宿</p>
        <p>合法民宿-南投縣民宿658號</p>
      </footer>
    </>
  );
}
