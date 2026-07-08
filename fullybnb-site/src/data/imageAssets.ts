import heroBuildingMainImage from "../assets/images/hero-building-main.jpg";
import heroCherryBlossomImage from "../assets/images/hero-cherry-blossom.jpg";
import heroLobbyCounterImage from "../assets/images/hero-lobby-counter.jpg";
import heroLoungeImage from "../assets/images/hero-lounge.jpg";
import heroMountainViewImage from "../assets/images/hero-mountain-view.jpg";
import heroPatioYardImage from "../assets/images/hero-patio-yard.jpg";
import heroPorchImage from "../assets/images/hero-porch.jpg";
import heroSignEntranceImage from "../assets/images/hero-sign-entrance.jpg";
import heroYardSwingsImage from "../assets/images/hero-yard-swings.jpg";
import logoImage from "../assets/images/kanban-logo-transparent.png";
import mapImage from "../assets/images/map.jpg";
import nearbyCampImage from "../assets/images/nearby-camp.jpg";
import nearbyChungTaiImage from "../assets/images/nearby-chung-tai.jpg";
import nearbyChocolateImage from "../assets/images/nearby-chocolate.jpg";
import nearbyDimuTempleImage from "../assets/images/nearby-dimu-temple.jpg";
import nearbyDuduIceImage from "../assets/images/nearby-dudu-ice.jpg";
import nearbyGuanyinWaterfallImage from "../assets/images/nearby-guanyin-waterfall.jpg";
import nearbyLakeImage from "../assets/images/nearby-lake.jpg";
import nearbyMarketStirFryImage from "../assets/images/nearby-market-stir-fry.jpg";
import nearbyPuliWineryImage from "../assets/images/nearby-puli-winery.jpg";
import nearbyYabiaoImage from "../assets/images/nearby-yabiao.jpg";
import berriesImage01 from "../assets/images/room-berries-01.jpg";
import berriesImage02 from "../assets/images/room-berries-02.jpg";
import berriesImage03 from "../assets/images/room-berries-03.jpg";
import berriesImage04 from "../assets/images/room-berries-04.jpg";
import berriesImage05 from "../assets/images/room-berries-05.jpg";
import daoImage01 from "../assets/images/room-dao-01.jpg";
import daoImage02 from "../assets/images/room-dao-02.jpg";
import daoImage03 from "../assets/images/room-dao-03.jpg";
import sunmoonImage01 from "../assets/images/room-sunmoon-01.jpg";
import sunmoonImage02 from "../assets/images/room-sunmoon-02.jpg";
import sunmoonImage03 from "../assets/images/room-sunmoon-03.jpg";
import woodImage01 from "../assets/images/room-wood-01.jpg";
import woodImage02 from "../assets/images/room-wood-02.jpg";
import breakfastImage from "../assets/images/story-breakfast.jpg";
import grassYardImage from "../assets/images/story-grass-yard.jpg";
import naturePathImage from "../assets/images/story-nature-path.jpg";

const imageModules: Record<string, string> = {
  "../assets/images/hero-building-main.jpg": heroBuildingMainImage,
  "../assets/images/hero-cherry-blossom.jpg": heroCherryBlossomImage,
  "../assets/images/hero-lobby-counter.jpg": heroLobbyCounterImage,
  "../assets/images/hero-lounge.jpg": heroLoungeImage,
  "../assets/images/hero-mountain-view.jpg": heroMountainViewImage,
  "../assets/images/hero-patio-yard.jpg": heroPatioYardImage,
  "../assets/images/hero-porch.jpg": heroPorchImage,
  "../assets/images/hero-sign-entrance.jpg": heroSignEntranceImage,
  "../assets/images/hero-yard-swings.jpg": heroYardSwingsImage,
  "../assets/images/kanban-logo-transparent.png": logoImage,
  "../assets/images/map.jpg": mapImage,
  "../assets/images/nearby-camp.jpg": nearbyCampImage,
  "../assets/images/nearby-chung-tai.jpg": nearbyChungTaiImage,
  "../assets/images/nearby-chocolate.jpg": nearbyChocolateImage,
  "../assets/images/nearby-dimu-temple.jpg": nearbyDimuTempleImage,
  "../assets/images/nearby-dudu-ice.jpg": nearbyDuduIceImage,
  "../assets/images/nearby-guanyin-waterfall.jpg": nearbyGuanyinWaterfallImage,
  "../assets/images/nearby-lake.jpg": nearbyLakeImage,
  "../assets/images/nearby-market-stir-fry.jpg": nearbyMarketStirFryImage,
  "../assets/images/nearby-puli-winery.jpg": nearbyPuliWineryImage,
  "../assets/images/nearby-yabiao.jpg": nearbyYabiaoImage,
  "../assets/images/room-berries-01.jpg": berriesImage01,
  "../assets/images/room-berries-02.jpg": berriesImage02,
  "../assets/images/room-berries-03.jpg": berriesImage03,
  "../assets/images/room-berries-04.jpg": berriesImage04,
  "../assets/images/room-berries-05.jpg": berriesImage05,
  "../assets/images/room-dao-01.jpg": daoImage01,
  "../assets/images/room-dao-02.jpg": daoImage02,
  "../assets/images/room-dao-03.jpg": daoImage03,
  "../assets/images/room-sunmoon-01.jpg": sunmoonImage01,
  "../assets/images/room-sunmoon-02.jpg": sunmoonImage02,
  "../assets/images/room-sunmoon-03.jpg": sunmoonImage03,
  "../assets/images/room-wood-01.jpg": woodImage01,
  "../assets/images/room-wood-02.jpg": woodImage02,
  "../assets/images/story-breakfast.jpg": breakfastImage,
  "../assets/images/story-grass-yard.jpg": grassYardImage,
  "../assets/images/story-nature-path.jpg": naturePathImage,
};

export function resolveImagePath(path: string) {
  const image = imageModules[path];

  if (!image) {
    throw new Error(`Missing image asset in siteConfig.json: ${path}`);
  }

  return image;
}
