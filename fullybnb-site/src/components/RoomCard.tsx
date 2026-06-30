import { Phone } from "lucide-react";
import type { Room } from "../data/rooms";

type Props = {
  room: Room;
};

export function RoomCard({ room }: Props) {
  return (
    <article className="room-card">
      <img src={room.image} alt={`${room.name}${room.category}`} />
      <div className="room-card-body">
        <div>
          <p className="eyebrow">{room.category}</p>
          <h3>{room.name}</h3>
          <p className="muted">{room.capacity}</p>
        </div>
        <div className="price-row" aria-label="房價">
          <span>平日 {room.weekdayPrice}</span>
          <span>假日 {room.holidayPrice}</span>
        </div>
        <ul className="tag-list" aria-label="房型特色">
          {room.highlights.map((highlight) => (
            <li key={highlight}>{highlight}</li>
          ))}
        </ul>
        <a className="text-button" href="tel:0932929748">
          <Phone size={17} aria-hidden="true" />
          詢問此房型
        </a>
      </div>
    </article>
  );
}
