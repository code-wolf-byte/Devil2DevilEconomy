const VIDEO_EXTENSIONS = [".mov", ".mp4", ".webm", ".ogg", ".avi"];

function isVideoUrl(url) {
  if (!url) return false;
  const lowerUrl = url.toLowerCase();
  return VIDEO_EXTENSIONS.some((ext) => lowerUrl.endsWith(ext));
}

function getPrimaryMedia(product) {
  if (product?.media?.length) {
    const primary = product.media.find((item) => item.is_primary);
    const media = primary || product.media[0];
    return { url: media.url, isVideo: media.type === "video" || isVideoUrl(media.url) };
  }
  if (product?.image_url) {
    return { url: product.image_url, isVideo: isVideoUrl(product.image_url) };
  }
  return { url: null, isVideo: false };
}

export default function ProductCard({
  product,
  linkTo,
}) {
  const formatTags = () => {
    const tags = [];

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
  const { url: mediaUrl, isVideo } = getPrimaryMedia(product);

  if (isVideo) {
    return (
      <a
        className="text-decoration-none text-reset d-block h-100"
        href={href}
      >
        <div className="store-card h-100 card border">
          <div className="card-img-top-wrapper" style={{ aspectRatio: "1/1", overflow: "hidden" }}>
            <video
              src={mediaUrl}
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
            <div className="d-flex flex-wrap gap-1 align-items-center">
              <span className="badge bg-dark d-inline-flex align-items-center gap-1" aria-label={`Price ${product.price}`}>
                <img src="/static/Coin_Gold.png" alt="" style={{ width: "14px", height: "14px" }} />
                {product.price}
              </span>
              {formatTags().map((tag, index) => (
                <span
                  key={index}
                  className={`badge bg-${tag.color === "gray" ? "secondary" : "light text-dark border"}`}
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
      <div className="store-card h-100 card border">
        {mediaUrl ? (
          <div style={{ aspectRatio: "1/1", overflow: "hidden" }}>
            <img
              src={mediaUrl}
              alt={product.name}
              className="card-img-top"
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
          </div>
        ) : null}
        <div className="card-body">
          <h5 className="card-title fw-bold">{product.name}</h5>
          <p className="card-text text-muted small">
            {product.description || "No description available."}
          </p>
        </div>

        <div className="card-body pt-0">
          <div className="d-flex flex-wrap gap-1 align-items-center">
            <span className="badge bg-dark d-inline-flex align-items-center gap-1" aria-label={`Price ${product.price}`}>
              <img src="/static/Coin_Gold.png" alt="" style={{ width: "14px", height: "14px" }} />
              {product.price}
            </span>
            {formatTags().map((tag, index) => (
              <span
                key={index}
                className={`badge bg-${tag.color === "gray" ? "secondary" : tag.color === "dark" ? "dark" : "light text-dark border"}`}
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
