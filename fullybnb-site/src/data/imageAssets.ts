import heroBuildingMainImage from "../assets/images/hero-building-main.webp";
import heroCherryBlossomImage from "../assets/images/hero-cherry-blossom.webp";
import heroLobbyCounterImage from "../assets/images/hero-lobby-counter.webp";
import heroLoungeImage from "../assets/images/hero-lounge.webp";
import heroMountainViewImage from "../assets/images/hero-mountain-view.webp";
import heroPatioYardImage from "../assets/images/hero-patio-yard.webp";
import heroPorchImage from "../assets/images/hero-porch.webp";
import heroSignEntranceImage from "../assets/images/hero-sign-entrance.webp";
import heroYardSwingsImage from "../assets/images/hero-yard-swings.webp";
import logoImage from "../assets/images/kanban-logo-transparent.png";
import mapImage from "../assets/images/map.webp";
import nearbyCampImage from "../assets/images/nearby-camp.webp";
import nearbyChungTaiImage from "../assets/images/nearby-chung-tai.webp";
import nearbyChocolateImage from "../assets/images/nearby-chocolate.webp";
import nearbyDimuTempleImage from "../assets/images/nearby-dimu-temple.webp";
import nearbyDuduIceImage from "../assets/images/nearby-dudu-ice.webp";
import nearbyGuanyinWaterfallImage from "../assets/images/nearby-guanyin-waterfall.webp";
import nearbyLakeImage from "../assets/images/nearby-lake.webp";
import nearbyMarketStirFryImage from "../assets/images/nearby-market-stir-fry.webp";
import nearbyPuliWineryImage from "../assets/images/nearby-puli-winery.webp";
import nearbyYabiaoImage from "../assets/images/nearby-yabiao.webp";
import berriesImage01 from "../assets/images/room-berries-01.webp";
import berriesImage02 from "../assets/images/room-berries-02.webp";
import berriesImage03 from "../assets/images/room-berries-03.webp";
import berriesImage04 from "../assets/images/room-berries-04.webp";
import berriesImage05 from "../assets/images/room-berries-05.webp";
import daoImage01 from "../assets/images/room-dao-01.webp";
import daoImage02 from "../assets/images/room-dao-02.webp";
import daoImage03 from "../assets/images/room-dao-03.webp";
import sunmoonImage01 from "../assets/images/room-sunmoon-01.webp";
import sunmoonImage02 from "../assets/images/room-sunmoon-02.webp";
import sunmoonImage03 from "../assets/images/room-sunmoon-03.webp";
import woodImage01 from "../assets/images/room-wood-01.webp";
import woodImage02 from "../assets/images/room-wood-02.webp";
import breakfastImage from "../assets/images/story-breakfast.webp";
import grassYardImage from "../assets/images/story-grass-yard.webp";
import naturePathImage from "../assets/images/story-nature-path.webp";

const imageModules: Record<string, string> = {
  "../assets/images/hero-building-main.webp": heroBuildingMainImage,
  "../assets/images/hero-cherry-blossom.webp": heroCherryBlossomImage,
  "../assets/images/hero-lobby-counter.webp": heroLobbyCounterImage,
  "../assets/images/hero-lounge.webp": heroLoungeImage,
  "../assets/images/hero-mountain-view.webp": heroMountainViewImage,
  "../assets/images/hero-patio-yard.webp": heroPatioYardImage,
  "../assets/images/hero-porch.webp": heroPorchImage,
  "../assets/images/hero-sign-entrance.webp": heroSignEntranceImage,
  "../assets/images/hero-yard-swings.webp": heroYardSwingsImage,
  "../assets/images/kanban-logo-transparent.png": logoImage,
  "../assets/images/map.webp": mapImage,
  "../assets/images/nearby-camp.webp": nearbyCampImage,
  "../assets/images/nearby-chung-tai.webp": nearbyChungTaiImage,
  "../assets/images/nearby-chocolate.webp": nearbyChocolateImage,
  "../assets/images/nearby-dimu-temple.webp": nearbyDimuTempleImage,
  "../assets/images/nearby-dudu-ice.webp": nearbyDuduIceImage,
  "../assets/images/nearby-guanyin-waterfall.webp": nearbyGuanyinWaterfallImage,
  "../assets/images/nearby-lake.webp": nearbyLakeImage,
  "../assets/images/nearby-market-stir-fry.webp": nearbyMarketStirFryImage,
  "../assets/images/nearby-puli-winery.webp": nearbyPuliWineryImage,
  "../assets/images/nearby-yabiao.webp": nearbyYabiaoImage,
  "../assets/images/room-berries-01.webp": berriesImage01,
  "../assets/images/room-berries-02.webp": berriesImage02,
  "../assets/images/room-berries-03.webp": berriesImage03,
  "../assets/images/room-berries-04.webp": berriesImage04,
  "../assets/images/room-berries-05.webp": berriesImage05,
  "../assets/images/room-dao-01.webp": daoImage01,
  "../assets/images/room-dao-02.webp": daoImage02,
  "../assets/images/room-dao-03.webp": daoImage03,
  "../assets/images/room-sunmoon-01.webp": sunmoonImage01,
  "../assets/images/room-sunmoon-02.webp": sunmoonImage02,
  "../assets/images/room-sunmoon-03.webp": sunmoonImage03,
  "../assets/images/room-wood-01.webp": woodImage01,
  "../assets/images/room-wood-02.webp": woodImage02,
  "../assets/images/story-breakfast.webp": breakfastImage,
  "../assets/images/story-grass-yard.webp": grassYardImage,
  "../assets/images/story-nature-path.webp": naturePathImage,
};

export function resolveImagePath(path: string) {
  const image = imageModules[path];

  if (!image) {
    throw new Error(`Missing image asset in siteConfig.json: ${path}`);
  }

  return image;
}
