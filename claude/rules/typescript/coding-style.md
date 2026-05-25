---
paths:
  - "**/*.ts"
  - "**/*.tsx"
  - "**/*.js"
  - "**/*.jsx"
---
# TypeScript/JavaScript Coding Style

> Extends common/coding-style.md with TypeScript/JavaScript specifics.

## Types and Interfaces

### Public APIs

- Add parameter and return types to exported functions
- Let TypeScript infer obvious local variable types
- Extract repeated inline object shapes into named types/interfaces

### Interfaces vs. Type Aliases

- Use `interface` for object shapes that may be extended
- Use `type` for unions, intersections, tuples, mapped types
- Prefer string literal unions over `enum`

### Avoid `any`

- Avoid `any` in application code
- Use `unknown` for external/untrusted input, then narrow safely
- Use generics when a value's type depends on the caller

### React Props

- Define component props with a named `interface` or `type`
- Type callback props explicitly
- Do not use `React.FC` unless there is a specific reason

## Immutability

Use spread operator for immutable updates:

```typescript
// WRONG: Mutation
function updateUser(user: User, name: string): User {
  user.name = name
  return user
}

// CORRECT: Immutability
function updateUser(user: Readonly<User>, name: string): User {
  return { ...user, name }
}
```

## Error Handling

Use async/await with try-catch and narrow unknown errors safely:

```typescript
async function loadUser(userId: string): Promise<User> {
  try {
    return await riskyOperation(userId)
  } catch (error: unknown) {
    if (error instanceof Error) {
      throw new Error(error.message)
    }
    throw new Error('Unexpected error')
  }
}
```

## Input Validation

Use Zod for schema-based validation:

```typescript
import { z } from 'zod'

const userSchema = z.object({
  email: z.string().email(),
  age: z.number().int().min(0).max(150)
})

type UserInput = z.infer<typeof userSchema>
```

## Console.log

- No `console.log` statements in production code
- Use proper logging libraries instead
