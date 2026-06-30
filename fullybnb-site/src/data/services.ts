import { Bike, Coffee, Home, MapPinned, Sprout } from "lucide-react";
import type { LucideIcon } from "lucide-react";

export type Service = {
  title: string;
  description: string;
  Icon: LucideIcon;
};

export const services: Service[] = [
  {
    title: "有機早餐",
    description: "住宿附早餐，以簡單、舒服的家常風味開始埔里的一天。",
    Icon: Coffee,
  },
  {
    title: "免費單車借用",
    description: "入住期間可借用自行車，適合慢慢探索東埔村落與埔里鄉間道路。",
    Icon: Bike,
  },
  {
    title: "在地農產代購",
    description: "協助介紹筊白筍、香菇、金線蓮與木耳等鄰近農產。",
    Icon: Sprout,
  },
  {
    title: "包棟方案",
    description: "10 至 24 人可包棟，享有專屬室內空間、戶外草皮與自在聚會時間。",
    Icon: Home,
  },
  {
    title: "在地旅程建議",
    description: "依住宿天數、交通方式與同行人數，協助推薦埔里、日月潭與周邊路線。",
    Icon: MapPinned,
  },
];
