import daoImage from "../assets/images/room-dao.jpg";
import woodImage from "../assets/images/room-wood.jpg";
import berriesImage from "../assets/images/room-berries.jpg";
import sunmoonImage from "../assets/images/room-sunmoon.jpg";

export type Room = {
  name: string;
  category: string;
  capacity: string;
  weekdayPrice: string;
  holidayPrice: string;
  image: string;
  highlights: string[];
};

export const rooms: Room[] = [
  {
    name: "稻香",
    category: "雙人景觀套房",
    capacity: "2 人，可加床",
    weekdayPrice: "NT$2,200",
    holidayPrice: "NT$2,800",
    image: daoImage,
    highlights: ["景觀陽台", "樓中樓童趣設計", "櫻花木建材"],
  },
  {
    name: "森林",
    category: "雙人景觀套房",
    capacity: "2 人，可加床",
    weekdayPrice: "NT$2,200",
    holidayPrice: "NT$2,800",
    image: woodImage,
    highlights: ["山景陽台", "加大雙人床", "日式原木風格"],
  },
  {
    name: "藍莓 / 紅莓",
    category: "雙人景觀套房",
    capacity: "2 人，可加床",
    weekdayPrice: "NT$2,200",
    holidayPrice: "NT$2,800",
    image: berriesImage,
    highlights: ["景觀最佳", "雙人沙發", "白樺木家具"],
  },
  {
    name: "太陽 / 月亮",
    category: "四人家庭套房",
    capacity: "4 人，可加床",
    weekdayPrice: "NT$3,000",
    holidayPrice: "NT$3,600",
    image: sunmoonImage,
    highlights: ["家庭房型", "良好採光", "北美胡桃木和室"],
  },
];
