import { Card } from "@asu/unity-react-core";

const VIDEO_EXTENSIONS = [".mov", ".mp4", ".webm", ".ogg", ".avi"];

function isVideoUrl(url) {
  if (!url) return false;
  const lowerUrl = url.toLowerCase();
  return VIDEO_EXTENSIONS.some((ext) => lowerUrl.endsWith(ext));
}

export default function ProductCard({
  product,
  linkTo,
}) {
  const formatTags = () => {
    const tags = [
      {
        label: `${product.price}`,
        color: "dark",
        ariaLabel: `Price ${product.price}`,
      },
    ];

    if (product.is_unlimited) {
      tags.push({ label: "Unlimited stock", color: "gray" });
    } else if (product.in_stock) {
      tags.push({
        label: `In stock (${product.stock})`,
        color: "gray",
        ariaLabel: `In stock ${product.stock}`,
      });
    } else {
      tags.push({ label: "Out of stock", color: "dark" });
    }

    if (product.product_type) {
      tags.push({
        label: product.product_type.replace(/_/g, " "),
        color: "white",
      });
    }

    return tags;
  };

  const href = linkTo || `/product/${product.id}`;
  const hasVideo = isVideoUrl(product.image_url);

  if (hasVideo) {
    return (
      <a
        className="text-decoration-none text-reset d-block h-100"
        href={href}
      >
        <div className="store-card h-100 card border">
          <div className="card-img-top-wrapper" style={{ aspectRatio: "16/9", overflow: "hidden" }}>
            <video
              src={product.image_url}
              autoPlay
              loop
              muted
              playsInline
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
          </div>
          <div className="card-body">
            <h5 className="card-title fw-bold">{product.name}</h5>
            <p className="card-text text-muted small">
              {product.description || "No description available."}
            </p>
            <div className="d-flex flex-wrap gap-1">
              {formatTags().map((tag, index) => (
                <span
                  key={index}
                  className={`badge bg-${tag.color === "dark" ? "dark" : tag.color === "gray" ? "secondary" : "light text-dark border"}`}
                  aria-label={tag.ariaLabel}
                >
                  {tag.label}
                </span>
              ))}
            </div>
          </div>
        </div>
      </a>
    );
  }

  return (
    <a
      className="text-decoration-none text-reset d-block h-100"
      href={href}
    >
      <div className="store-card h-100">
        <Card
          type="default"
          horizontal={false}
          showBorders={true}
          image={product.image_url || undefined}
          imageAltText={product.name}
          title={product.name}
          body={product.description || "No description available."}
          tags={formatTags()}
        />
      </div>
    </a>
  );
}
