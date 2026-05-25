---
name: swiftui-components
description: SwiftUI component expert for building reusable views, custom modifiers, and view compositions. Use when creating new SwiftUI views or refactoring UI code.
---

# SwiftUI Components

## Instructions
1. Analyze the required component functionality
2. Check existing components for reuse
3. Follow project styling conventions
4. Use proper state management (@State, @Binding, @Observable)

## Patterns

### View Extraction
- Extract subviews when they exceed 50 lines
- Use ViewModifier for reusable styling
- Prefer composition over inheritance

### State Management
- @State for local view state
- @Bindable for @Observable object bindings
- @Environment for dependency injection

### Navigation
```swift
// Use NavigationStack with type-safe routing
enum Route: Hashable {
    case detail(Item)
    case settings
}

NavigationStack(path: $router.path) {
    ContentView()
        .navigationDestination(for: Route.self) { route in
            // Handle routing
        }
}
```

### Accessibility
- Always add accessibility labels
- Support Dynamic Type
- Test with VoiceOver
