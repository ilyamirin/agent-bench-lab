pub const OpenRouterClient = struct {
    provider: []const u8,
    model: []const u8,

    pub fn init(provider: []const u8, model: []const u8) OpenRouterClient {
        return .{
            .provider = provider,
            .model = model,
        };
    }
};
