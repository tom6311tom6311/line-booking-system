import { ChevronLeft, ChevronRight, Facebook, MapPin, Phone } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { PointerEvent, TouchEvent } from "react";
import { BookingSection } from "./components/BookingSection";
import { RoomCard } from "./components/RoomCard";
import { SectionHeading } from "./components/SectionHeading";
import { nearbyPlaces, rooms, siteContent } from "./data/siteContent";

const swipeMinimumDistance = 45;
const swipeIntentRatio = 1.2;
const heroAutoPauseDurationMs = 10000;

function getCircularActiveIndex(slideIndex: number, itemCount: number) {
  if (itemCount <= 0) {
    return 0;
  }

  return (slideIndex - 1 + itemCount) % itemCount;
}

function getCircularSlides<T>(items: T[]) {
  if (items.length <= 1) {
    return items;
  }

  return [items[items.length - 1], ...items, items[0]];
}

function shouldLoadCircularSlide(index: number, slideIndex: number) {
  return Math.abs(index - slideIndex) <= 1;
}

async function preloadImage(src?: string) {
  if (!src) {
    return;
  }

  const image = new Image();
  image.src = src;

  if (!image.complete) {
    await new Promise<void>((resolve) => {
      image.onload = () => resolve();
      image.onerror = () => resolve();
    });
  }

  await image.decode?.().catch(() => undefined);
}

function normalizeCircularSlideIndex(slideIndex: number, itemCount: number) {
  if (itemCount <= 1) {
    return slideIndex;
  }

  if (slideIndex <= 0) {
    return itemCount;
  }

  if (slideIndex >= itemCount + 1) {
    return 1;
  }

  return slideIndex;
}

function useSwipeNavigation(onPrevious: () => void, onNext: () => void, isEnabled: boolean) {
  const touchStartRef = useRef<{ x: number; y: number; width: number } | null>(null);
  const [dragOffset, setDragOffset] = useState(0);
  const [isDragging, setIsDragging] = useState(false);

  function handleTouchStart(event: TouchEvent) {
    if (!isEnabled) {
      return;
    }

    const touch = event.touches[0];
    touchStartRef.current = {
      x: touch.clientX,
      y: touch.clientY,
      width: event.currentTarget.clientWidth,
    };
    setIsDragging(true);
    setDragOffset(0);
  }

  function handleTouchMove(event: TouchEvent) {
    const start = touchStartRef.current;

    if (!isEnabled || !start) {
      return;
    }

    const touch = event.touches[0];
    const deltaX = touch.clientX - start.x;
    const deltaY = touch.clientY - start.y;
    const horizontalDistance = Math.abs(deltaX);

    if (horizontalDistance < Math.abs(deltaY) * swipeIntentRatio) {
      setDragOffset(0);
      return;
    }

    setDragOffset((deltaX / start.width) * 100);
  }

  function handleTouchEnd(event: TouchEvent) {
    const start = touchStartRef.current;
    touchStartRef.current = null;
    setIsDragging(false);
    setDragOffset(0);

    if (!isEnabled || !start) {
      return;
    }

    const touch = event.changedTouches[0];
    const deltaX = touch.clientX - start.x;
    const deltaY = touch.clientY - start.y;
    const horizontalDistance = Math.abs(deltaX);

    if (
      horizontalDistance < swipeMinimumDistance ||
      horizontalDistance < Math.abs(deltaY) * swipeIntentRatio
    ) {
      return;
    }

    if (deltaX > 0) {
      onPrevious();
    } else {
      onNext();
    }
  }

  function handleTouchCancel() {
    touchStartRef.current = null;
    setIsDragging(false);
    setDragOffset(0);
  }

  return {
    dragOffset,
    isDragging,
    touchHandlers: {
      onTouchStart: handleTouchStart,
      onTouchMove: handleTouchMove,
      onTouchEnd: handleTouchEnd,
      onTouchCancel: handleTouchCancel,
    },
  };
}

export function App() {
  const [heroSlideIndex, setHeroSlideIndex] = useState(1);
  const [storySlideIndex, setStorySlideIndex] = useState(1);
  const [nearbySlideIndex, setNearbySlideIndex] = useState(1);
  const [isHeroTransitioning, setIsHeroTransitioning] = useState(true);
  const [isStoryTransitioning, setIsStoryTransitioning] = useState(true);
  const [isNearbyTransitioning, setIsNearbyTransitioning] = useState(true);
  const [isHeroAutoPaused, setIsHeroAutoPaused] = useState(false);
  const heroAutoResumeTimeoutRef = useRef<number | null>(null);
  const [isPortraitViewport, setIsPortraitViewport] = useState(() =>
    window.matchMedia("(orientation: portrait)").matches,
  );
  const { site, assets, hero, intro, sections, bookingNote, footer } = siteContent;

  const heroSlides = hero.images.flatMap((image) => {
    if (!isPortraitViewport || !image.portraitSplit) {
      return [{ ...image, slideKey: image.src, slideClassName: "", imageClassName: "" }];
    }

    return [
      {
        ...image,
        slideKey: `${image.src}-portrait-left`,
        slideClassName: "hero-slide-split-left",
        imageClassName: "hero-image-split",
      },
      {
        ...image,
        slideKey: `${image.src}-portrait-right`,
        slideClassName: "hero-slide-split-right",
        imageClassName: "hero-image-split",
      },
    ];
  });
  const heroCount = heroSlides.length;
  const storyCount = intro.stories.length;
  const nearbyCount = nearbyPlaces.length;
  const heroIndex = getCircularActiveIndex(heroSlideIndex, heroCount);
  const storyIndex = getCircularActiveIndex(storySlideIndex, storyCount);
  const nearbyIndex = getCircularActiveIndex(nearbySlideIndex, nearbyCount);
  const circularHeroSlides = getCircularSlides(heroSlides);
  const circularStories = getCircularSlides(intro.stories);
  const circularNearbyPlaces = getCircularSlides(nearbyPlaces);
  const heroSwipeHandlers = useSwipeNavigation(showPreviousHero, showNextHero, heroCount > 1);
  const storySwipeHandlers = useSwipeNavigation(showPreviousStory, showNextStory, storyCount > 1);
  const nearbySwipeHandlers = useSwipeNavigation(showPreviousNearby, showNextNearby, nearbyCount > 1);

  useEffect(() => {
    const orientationQuery = window.matchMedia("(orientation: portrait)");

    function updateViewportOrientation(event: MediaQueryListEvent) {
      setIsPortraitViewport(event.matches);
    }

    setIsPortraitViewport(orientationQuery.matches);
    orientationQuery.addEventListener("change", updateViewportOrientation);

    return () => {
      orientationQuery.removeEventListener("change", updateViewportOrientation);
    };
  }, []);

  useEffect(() => {
    setHeroSlideIndex((current) => Math.min(Math.max(current, 1), Math.max(heroCount, 1)));
    setIsHeroTransitioning(false);
  }, [heroCount]);

  useEffect(() => {
    if (
      heroCount <= 1 ||
      isHeroAutoPaused ||
      window.matchMedia("(prefers-reduced-motion: reduce)").matches
    ) {
      return;
    }

    const intervalId = window.setInterval(() => {
      advanceNextHero();
    }, 5000);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [heroCount, isHeroAutoPaused]);

  useEffect(() => {
    return () => {
      if (heroAutoResumeTimeoutRef.current !== null) {
        window.clearTimeout(heroAutoResumeTimeoutRef.current);
      }
    };
  }, []);

  function pauseHeroAutomation() {
    if (heroCount <= 1) {
      return;
    }

    setIsHeroAutoPaused(true);

    if (heroAutoResumeTimeoutRef.current !== null) {
      window.clearTimeout(heroAutoResumeTimeoutRef.current);
    }

    heroAutoResumeTimeoutRef.current = window.setTimeout(() => {
      setIsHeroAutoPaused(false);
      heroAutoResumeTimeoutRef.current = null;
    }, heroAutoPauseDurationMs);
  }

  function showPreviousHero() {
    pauseHeroAutomation();
    setIsHeroTransitioning(true);
    setHeroSlideIndex((current) => normalizeCircularSlideIndex(current, heroCount) - 1);
  }

  function showNextHero() {
    pauseHeroAutomation();
    advanceNextHero();
  }

  async function showHeroSlide(index: number) {
    pauseHeroAutomation();
    const targetSlideIndex = index + 1;
    await preloadImage(circularHeroSlides[targetSlideIndex]?.src);
    setIsHeroTransitioning(true);
    setHeroSlideIndex(targetSlideIndex);
  }

  function advanceNextHero() {
    setIsHeroTransitioning(true);
    setHeroSlideIndex((current) => normalizeCircularSlideIndex(current, heroCount) + 1);
  }

  function showPreviousStory() {
    setIsStoryTransitioning(true);
    setStorySlideIndex((current) => normalizeCircularSlideIndex(current, storyCount) - 1);
  }

  function showNextStory() {
    setIsStoryTransitioning(true);
    setStorySlideIndex((current) => normalizeCircularSlideIndex(current, storyCount) + 1);
  }

  async function showStorySlide(index: number) {
    const targetSlideIndex = index + 1;
    await preloadImage(circularStories[targetSlideIndex]?.image);
    setIsStoryTransitioning(true);
    setStorySlideIndex(targetSlideIndex);
  }

  function showPreviousNearby() {
    setIsNearbyTransitioning(true);
    setNearbySlideIndex((current) => normalizeCircularSlideIndex(current, nearbyCount) - 1);
  }

  function showNextNearby() {
    setIsNearbyTransitioning(true);
    setNearbySlideIndex((current) => normalizeCircularSlideIndex(current, nearbyCount) + 1);
  }

  async function showNearbySlide(index: number) {
    const targetSlideIndex = index + 1;
    await preloadImage(circularNearbyPlaces[targetSlideIndex]?.image);
    setIsNearbyTransitioning(true);
    setNearbySlideIndex(targetSlideIndex);
  }

  function handleHeroTransitionEnd() {
    if (heroCount <= 1) {
      return;
    }

    if (heroSlideIndex === 0) {
      setIsHeroTransitioning(false);
      setHeroSlideIndex(heroCount);
    }

    if (heroSlideIndex === heroCount + 1) {
      setIsHeroTransitioning(false);
      setHeroSlideIndex(1);
    }
  }

  function handleStoryTransitionEnd() {
    if (storyCount <= 1) {
      return;
    }

    if (storySlideIndex === 0) {
      setIsStoryTransitioning(false);
      setStorySlideIndex(storyCount);
    }

    if (storySlideIndex === storyCount + 1) {
      setIsStoryTransitioning(false);
      setStorySlideIndex(1);
    }
  }

  function handleNearbyTransitionEnd() {
    if (nearbyCount <= 1) {
      return;
    }

    if (nearbySlideIndex === 0) {
      setIsNearbyTransitioning(false);
      setNearbySlideIndex(nearbyCount);
    }

    if (nearbySlideIndex === nearbyCount + 1) {
      setIsNearbyTransitioning(false);
      setNearbySlideIndex(1);
    }
  }

  function clearClickedButtonFocus(event: PointerEvent<HTMLElement>) {
    const target = event.target;

    if (!(target instanceof Element)) {
      return;
    }

    target.closest("button")?.blur();
  }

  return (
    <>
      <main id="top" onPointerUpCapture={clearClickedButtonFocus}>
        <section className="hero" aria-label={hero.ariaLabel} {...heroSwipeHandlers.touchHandlers}>
          <div
            className="hero-slides"
            style={{
              transform: `translateX(calc(-${heroSlideIndex * 100}% + ${heroSwipeHandlers.dragOffset}%))`,
              transition: heroSwipeHandlers.isDragging || !isHeroTransitioning ? "none" : undefined,
            }}
            onTransitionEnd={handleHeroTransitionEnd}
          >
            {circularHeroSlides.map((image, index) => {
              const shouldLoadImage = shouldLoadCircularSlide(index, heroSlideIndex);

              return (
                <div
                  className={`hero-slide ${image.slideClassName}`.trim()}
                  key={`${image.slideKey}-${index}`}
                  aria-hidden={index !== heroSlideIndex}
                >
                  {shouldLoadImage ? (
                    <img
                      className={`hero-image ${image.imageClassName}`.trim()}
                      src={image.src}
                      alt={image.alt}
                      loading="eager"
                      decoding="async"
                    />
                  ) : (
                    <div className="hero-image-placeholder" aria-hidden="true" />
                  )}
                </div>
              );
            })}
          </div>
          <div className="hero-overlay" />
          <div className="carousel-dots hero-carousel-dots" aria-label="民宿照片頁數">
            {heroSlides.map((image, index) => (
              <button
                key={image.slideKey}
                type="button"
                className={index === heroIndex ? "is-active" : ""}
                onClick={() => {
                  showHeroSlide(index);
                }}
                aria-label={`查看第 ${index + 1} 張民宿照片`}
                aria-current={index === heroIndex}
              />
            ))}
          </div>
          <div className="hero-content">
            <p className="eyebrow">{hero.eyebrow}</p>
            <h1>{hero.title}</h1>
            <p>{hero.description}</p>
            <div className="hero-actions">
              <a className="primary-button" href={hero.primaryCtaHref}>
                {hero.primaryCtaLabel}
              </a>
              <a className="secondary-button" href={hero.secondaryCtaHref}>
                {hero.secondaryCtaLabel}
              </a>
            </div>
          </div>
        </section>

        <section className="intro-section">
          <div className="intro-copy">
            <p className="eyebrow">{intro.eyebrow}</p>
            <h2>{intro.title}</h2>
            <p>{intro.description}</p>
            <div className="story-carousel" aria-label={intro.storyAriaLabel}>
              <div className="story-viewport" {...storySwipeHandlers.touchHandlers}>
                <div
                  className="story-track"
                  style={{
                    transform: `translateX(calc(-${storySlideIndex * 100}% + ${storySwipeHandlers.dragOffset}%))`,
                    transition: storySwipeHandlers.isDragging || !isStoryTransitioning ? "none" : undefined,
                  }}
                  onTransitionEnd={handleStoryTransitionEnd}
                >
                  {circularStories.map((story, index) => {
                    const shouldLoadImage = shouldLoadCircularSlide(index, storySlideIndex);

                    return (
                      <article key={`${story.title}-${index}`} aria-hidden={index !== storySlideIndex}>
                        <div>
                          <h3>{story.title}</h3>
                          <p>{story.description}</p>
                        </div>
                        {shouldLoadImage ? (
                          <img src={story.image} alt={story.imageAlt} loading="eager" decoding="async" />
                        ) : (
                          <div className="story-image-placeholder" aria-hidden="true" />
                        )}
                      </article>
                    );
                  })}
                </div>
                <div className="story-carousel-controls">
                  <button
                    className="carousel-button carousel-button-previous story-carousel-button"
                    type="button"
                    onClick={showPreviousStory}
                    aria-label="上一則民宿故事"
                  >
                    <ChevronLeft size={20} aria-hidden="true" />
                  </button>
                  <button
                    className="carousel-button carousel-button-next story-carousel-button"
                    type="button"
                    onClick={showNextStory}
                    aria-label="下一則民宿故事"
                  >
                    <ChevronRight size={20} aria-hidden="true" />
                  </button>
                </div>
                <div className="carousel-dots story-carousel-dots" aria-label="民宿故事頁數">
                  {intro.stories.map((story, index) => (
                    <button
                      key={story.title}
                      type="button"
                      className={index === storyIndex ? "is-active" : ""}
                      onClick={() => {
                        showStorySlide(index);
                      }}
                      aria-label={`查看${story.title}`}
                      aria-current={index === storyIndex}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="section" id="rooms">
          <SectionHeading eyebrow={sections.rooms.eyebrow} title={sections.rooms.title} />
          <div className="booking-note">
            <strong>{bookingNote.lead}</strong>
            <span>{bookingNote.description}</span>
          </div>
          <div className="room-grid">
            {rooms.map((room) => (
              <RoomCard key={room.name} room={room} />
            ))}
          </div>
        </section>

        <BookingSection />

        <section className="section" id="nearby">
          <SectionHeading eyebrow={sections.nearby.eyebrow} title={sections.nearby.title}>
            {sections.nearby.description}
          </SectionHeading>
          <div className="nearby-carousel" aria-label={sections.nearby.title}>
            <div className="nearby-viewport" {...nearbySwipeHandlers.touchHandlers}>
              <div
                className="nearby-track"
                style={{
                  transform: `translateX(calc(-${nearbySlideIndex * 100}% + ${nearbySwipeHandlers.dragOffset}%))`,
                  transition: nearbySwipeHandlers.isDragging || !isNearbyTransitioning ? "none" : undefined,
                }}
                onTransitionEnd={handleNearbyTransitionEnd}
              >
                {circularNearbyPlaces.map((place, index) => {
                  const shouldLoadImage = shouldLoadCircularSlide(index, nearbySlideIndex);

                  return (
                    <article className="nearby-card" key={`${place.name}-${index}`} aria-hidden={index !== nearbySlideIndex}>
                      <div className="nearby-card-media">
                        {shouldLoadImage ? (
                          <img src={place.image} alt={place.name} loading="eager" decoding="async" />
                        ) : (
                          <div className="nearby-image-placeholder" aria-hidden="true" />
                        )}
                      </div>
                      <div className="nearby-card-content">
                        <p className="eyebrow">{place.category}</p>
                        <h3>{place.name}</h3>
                        <p>{place.description}</p>
                        <span>{place.distance}</span>
                      </div>
                    </article>
                  );
                })}
              </div>
              <div className="nearby-carousel-overlay">
                <button
                  className="carousel-button carousel-button-previous nearby-carousel-button"
                  type="button"
                  onClick={showPreviousNearby}
                  aria-label="上一個附近景點"
                >
                  <ChevronLeft size={20} aria-hidden="true" />
                </button>
                <button
                  className="carousel-button carousel-button-next nearby-carousel-button"
                  type="button"
                  onClick={showNextNearby}
                  aria-label="下一個附近景點"
                >
                  <ChevronRight size={20} aria-hidden="true" />
                </button>
                <div className="carousel-dots nearby-carousel-dots" aria-label="附近景點頁數">
                  {nearbyPlaces.map((dotPlace, dotIndex) => (
                    <button
                      key={dotPlace.name}
                      type="button"
                      className={dotIndex === nearbyIndex ? "is-active" : ""}
                      onClick={() => {
                        showNearbySlide(dotIndex);
                      }}
                      aria-label={`查看${dotPlace.name}`}
                      aria-current={dotIndex === nearbyIndex}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="section traffic-section" id="traffic">
          <div>
            <SectionHeading eyebrow={sections.traffic.eyebrow} title={sections.traffic.title}>
              {sections.traffic.description}
            </SectionHeading>
            <div className="contact-list">
              <a
                href={site.mapUrl}
                target="_blank"
                rel="noreferrer"
              >
                <MapPin size={19} aria-hidden="true" />
                {site.address}
              </a>
            </div>
          </div>
          <div className="map-card">
            <img
              src={assets.map}
              alt={`${site.name}簡易地圖`}
              width={1313}
              height={1400}
              loading="lazy"
              decoding="async"
            />
            <a href={site.mapUrl} target="_blank" rel="noreferrer">
              <MapPin size={18} aria-hidden="true" />
              開啟地圖
            </a>
          </div>
        </section>
      </main>
      <footer className="site-footer">
        <p>{footer.name}</p>
        <p>{footer.license}</p>
        <div className="footer-links">
          <a href={site.phoneHref}>
            <Phone size={18} aria-hidden="true" />
            {site.ownerContact}
          </a>
          <a href={site.facebookUrl} target="_blank" rel="noreferrer">
            <Facebook size={18} aria-hidden="true" />
            {site.facebookLabel}
          </a>
        </div>
      </footer>
    </>
  );
}
