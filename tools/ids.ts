/** An asset id, a variant, a family or a tag: lower `snake_case`, starting with a letter. */
export const SNAKE = /^[a-z][a-z0-9]*(_[a-z0-9]+)*$/;

export const isSnake = (value: string): boolean => SNAKE.test(value);

/** A variant id belongs to an asset when it is the asset id or extends it with `_<suffix>`. */
export const isVariantOf = (variant: string, id: string): boolean =>
  isSnake(variant) && (variant === id || variant.startsWith(`${id}_`));
