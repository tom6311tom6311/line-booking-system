import rawConfig from "./siteConfig.json";
import { resolveImagePath } from "./imageAssets";

export type Room = {
  name: string;
  category: string;
  weekdayPrice: string;
  holidayPrice: string;
  extraBedPrice: string;
  images: string[];
  highlights: string[];
};

export type NearbyPlace = {
  name: string;
  category: string;
  distance: string;
  image: string;
  description: string;
};

const intro = {
  ...rawConfig.intro,
  stories: rawConfig.intro.stories.map((story) => ({
    ...story,
    image: resolveImagePath(story.image),
  })),
};

const hero = {
  ...rawConfig.hero,
  images: rawConfig.hero.images.map((image) => ({
    ...image,
    src: resolveImagePath(image.src),
  })),
};

const assets = {
  logo: resolveImagePath(rawConfig.assets.logo),
  map: resolveImagePath(rawConfig.assets.map),
};

export const rooms: Room[] = rawConfig.rooms.map((room) => ({
  ...room,
  images: room.images.map(resolveImagePath),
}));

export const nearbyPlaces: NearbyPlace[] = rawConfig.nearbyPlaces.map((place) => ({
  ...place,
  image: resolveImagePath(place.image),
}));

export const siteContent = {
  ...rawConfig,
  assets,
  hero,
  intro,
  rooms,
  nearbyPlaces,
};
