import { ChevronLeft, ChevronRight } from "lucide-react";
import { useRef, useState } from "react";
import type { TouchEvent } from "react";
import { siteContent } from "../data/siteContent";

type Props = {
  images: string[];
  label: string;
};

const swipeMinimumDistance = 45;
const swipeIntentRatio = 1.2;

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

function shouldLoadSlide(index: number, slideIndex: number) {
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

export function ImageCarousel({ images, label }: Props) {
  const hasMultipleImages = images.length > 1;
  const [slideIndex, setSlideIndex] = useState(hasMultipleImages ? 1 : 0);
  const [isTransitioning, setIsTransitioning] = useState(true);
  const [dragOffset, setDragOffset] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const touchStartRef = useRef<{ x: number; y: number; width: number } | null>(null);
  const { carousel } = siteContent;

  const slides = hasMultipleImages ? [images[images.length - 1], ...images, images[0]] : images;
  const activeIndex = hasMultipleImages
    ? (slideIndex - 1 + images.length) % images.length
    : 0;

  function showPrevious() {
    setIsTransitioning(true);
    setSlideIndex((current) => normalizeCircularSlideIndex(current, images.length) - 1);
  }

  function showNext() {
    setIsTransitioning(true);
    setSlideIndex((current) => normalizeCircularSlideIndex(current, images.length) + 1);
  }

  async function showSlide(index: number) {
    await preloadImage(images[index]);
    setIsTransitioning(true);
    setSlideIndex(index + 1);
  }

  function handleTouchStart(event: TouchEvent) {
    if (!hasMultipleImages) {
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

    if (!hasMultipleImages || !start) {
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

    if (!hasMultipleImages || !start) {
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
      showPrevious();
    } else {
      showNext();
    }
  }

  function handleTouchCancel() {
    touchStartRef.current = null;
    setIsDragging(false);
    setDragOffset(0);
  }

  function handleTransitionEnd() {
    if (!hasMultipleImages) {
      return;
    }

    if (slideIndex === 0) {
      setIsTransitioning(false);
      setSlideIndex(images.length);
    }

    if (slideIndex === images.length + 1) {
      setIsTransitioning(false);
      setSlideIndex(1);
    }
  }

  return (
    <div
      className="image-carousel"
      aria-label={`${label}${carousel.imageSuffix}`}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      onTouchCancel={handleTouchCancel}
    >
      <div
        className="carousel-slides"
        style={{
          transform: `translateX(calc(-${slideIndex * 100}% + ${dragOffset}%))`,
          transition: isTransitioning && !isDragging ? undefined : "none",
        }}
        onTransitionEnd={handleTransitionEnd}
      >
        {slides.map((image, index) => {
          const shouldLoadImage = shouldLoadSlide(index, slideIndex);
          const imageIndex = hasMultipleImages
            ? index === 0
              ? images.length - 1
              : index === slides.length - 1
                ? 0
                : index - 1
            : 0;

          return (
            shouldLoadImage ? (
              <img
                key={`${image}-${index}`}
                src={image}
                alt={`${label}${carousel.imageSuffix} ${imageIndex + 1}`}
                aria-hidden={hasMultipleImages && index !== slideIndex}
                loading="eager"
                decoding="async"
              />
            ) : (
              <div
                aria-hidden="true"
                className="carousel-image-placeholder"
                key={`${image}-${index}`}
              />
            )
          );
        })}
      </div>
      {hasMultipleImages && (
        <>
          <button
            className="carousel-button carousel-button-previous"
            type="button"
            onClick={showPrevious}
            aria-label={`${carousel.previousPrefix}${label}${carousel.imageSuffix}`}
          >
            <ChevronLeft size={20} aria-hidden="true" />
          </button>
          <button
            className="carousel-button carousel-button-next"
            type="button"
            onClick={showNext}
            aria-label={`${carousel.nextPrefix}${label}${carousel.imageSuffix}`}
          >
            <ChevronRight size={20} aria-hidden="true" />
          </button>
          <div className="carousel-dots" aria-label={carousel.paginationAriaLabel}>
            {images.map((image, index) => (
              <button
                key={image}
                type="button"
                className={index === activeIndex ? "is-active" : ""}
                onClick={() => showSlide(index)}
                aria-label={`${carousel.goToPrefix} ${index + 1} ${carousel.goToSuffix}${label}${carousel.imageSuffix}`}
                aria-current={index === activeIndex}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
