type PhoneLinkedTextProps = {
  text: string;
  phoneHref: string;
  phrases?: string[];
};

function escapeRegExp(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export function PhoneLinkedText({
  text,
  phoneHref,
  phrases = ["電話預約", "來電"],
}: PhoneLinkedTextProps) {
  const matcher = new RegExp(`(${phrases.map(escapeRegExp).join("|")})`, "g");

  return (
    <>
      {text.split(matcher).map((part, index) =>
        phrases.includes(part) ? (
          <a className="phone-inline-link" href={phoneHref} key={`${part}-${index}`}>
            {part}
          </a>
        ) : (
          part
        ),
      )}
    </>
  );
}
