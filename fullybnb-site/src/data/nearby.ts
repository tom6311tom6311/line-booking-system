import campImage from "../assets/images/nearby-camp.jpg";
import chocolateImage from "../assets/images/nearby-chocolate.jpg";
import lakeImage from "../assets/images/nearby-lake.jpg";

export type NearbyPlace = {
  name: string;
  category: string;
  distance: string;
  image: string;
  description: string;
};

export const nearbyPlaces: NearbyPlace[] = [
  {
    name: "聽瀑營地",
    category: "自然野趣",
    distance: "開車 5-10 分鐘",
    image: campImage,
    description: "溪邊玩水、露營與季節賞螢的附近景點。",
  },
  {
    name: "鯉魚潭",
    category: "親子景點",
    distance: "埔里周邊",
    image: lakeImage,
    description: "湖畔散步、親山步道與筊白筍特色伴手禮。",
  },
  {
    name: "18 度 C 巧克力工房",
    category: "埔里美食",
    distance: "埔里市區",
    image: chocolateImage,
    description: "埔里人氣甜點景點，適合安排在市區覓食行程中。",
  },
];
