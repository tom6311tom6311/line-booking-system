import { CalendarCheck } from "lucide-react";
import { ImageCarousel } from "./ImageCarousel";
import { siteContent, type Room } from "../data/siteContent";

type Props = {
  room: Room;
};

export function RoomCard({ room }: Props) {
  const { roomCard } = siteContent;
  const bookingHref = `#booking${room.roomIds?.length ? `?roomIds=${encodeURIComponent(room.roomIds.join(","))}` : ""}`;

  function handleBookingClick() {
    window.setTimeout(() => {
      window.dispatchEvent(new Event("hashchange"));
    }, 0);
  }

  return (
    <article className="room-card">
      <ImageCarousel images={room.images} label={`${room.name}${room.category}`} />
      <div className="room-card-body">
        <div>
          <p className="eyebrow">{room.category}</p>
          <h3>{room.name}</h3>
        </div>
        <div className="price-row" aria-label={roomCard.priceAriaLabel}>
          <span>
            {roomCard.weekdayPrefix} {room.weekdayPrice}
          </span>
          <span>
            {roomCard.holidayPrefix} {room.holidayPrice}
          </span>
        </div>
        <div className="room-price-note">
          <span>{roomCard.breakfastIncludedLabel}</span>
          <span>
            {roomCard.extraBedPrefix} {room.extraBedPrice}
          </span>
        </div>
        <ul className="tag-list" aria-label={roomCard.featuresAriaLabel}>
          {room.highlights.map((highlight) => (
            <li key={highlight}>{highlight}</li>
          ))}
        </ul>
        {room.specialNotes?.length ? (
          <ul className="room-special-notes">
            {room.specialNotes.map((note) => (
              <li key={note.roomId}>
                {note.text}
              </li>
            ))}
          </ul>
        ) : null}
        <a className="text-button" href={bookingHref} onClick={handleBookingClick}>
          <CalendarCheck size={17} aria-hidden="true" />
          {roomCard.ctaLabel}
        </a>
      </div>
    </article>
  );
}
