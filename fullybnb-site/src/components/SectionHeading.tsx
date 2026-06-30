type Props = {
  eyebrow: string;
  title: string;
  children: string;
};

export function SectionHeading({ eyebrow, title, children }: Props) {
  return (
    <div className="section-heading">
      <p className="eyebrow">{eyebrow}</p>
      <h2>{title}</h2>
      <p>{children}</p>
    </div>
  );
}
