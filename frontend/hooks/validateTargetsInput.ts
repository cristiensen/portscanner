export default function validateTargetsInput(raw: string): string | null {
  if (!raw.trim()) return null;

  const parts = raw
    .split(",")
    .map((p) => p.trim())
    .filter(Boolean);

  const ipv4Segment = "(25[0-5]|2[0-4]\\d|1\\d\\d|[1-9]\\d|\\d)";
  const ipv4 = `${ipv4Segment}\\.${ipv4Segment}\\.${ipv4Segment}\\.${ipv4Segment}`;
  const cidr = new RegExp(`^${ipv4}\\/(\\d|[1-2]\\d|3[0-2])$`);
  const singleIp = new RegExp(`^${ipv4}$`);
  const fullRange = new RegExp(`^${ipv4}-${ipv4}$`);
  const shortRange = new RegExp(
    `^${ipv4}-(\\d|[1-9]\\d|1\\d\\d|2[0-4]\\d|25[0-5])$`,
  );

  for (const part of parts) {
    if (
      cidr.test(part) ||
      singleIp.test(part) ||
      fullRange.test(part) ||
      shortRange.test(part)
    ) {
      continue;
    }
    return `"${part}" is not a valid IPv4 address, range, or CIDR subnet.`;
  }

  return null;
}
