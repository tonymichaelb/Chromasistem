import { Link } from "react-router-dom"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Field, FieldGroup, FieldLabel, FieldDescription } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import {
  InputGroup,
  InputGroupInput,
  InputGroupAddon,
  InputGroupButton,
} from "@/components/ui/input-group"
import { cn } from "@/lib/utils"
import { useRegister } from "./hook"
import { HugeiconsIcon } from "@hugeicons/react"
import { EyeIcon, ViewOffIcon } from "@hugeicons/core-free-icons"

export function Register() {
  const {
    username,
    setUsername,
    password,
    setPassword,
    confirmPassword,
    setConfirmPassword,
    showPassword,
    setShowPassword,
    showConfirmPassword,
    setShowConfirmPassword,
    message,
    loading,
    handleSubmit,
  } = useRegister()

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-muted/30 p-3 sm:p-4">
      <Card className="w-full max-w-sm min-w-0">
        <CardHeader className="text-center space-y-2">
          <div className="flex justify-center">
            <img
              src="/images/logo-branca.png"
              alt="Croma Logo"
              className="h-14 w-auto object-contain dark:invert"
            />
          </div>
          <CardTitle className="text-2xl">Criar Conta</CardTitle>
          <CardDescription>Sistema Croma</CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4 pb-6">
            <FieldGroup>
              <Field>
                <FieldLabel htmlFor="register-username">Usuário</FieldLabel>
                <Input
                  id="register-username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  autoComplete="username"
                  required
                />
              </Field>
              <Field>
                <FieldLabel htmlFor="register-password">Senha</FieldLabel>
                <InputGroup>
                  <InputGroupInput
                    id="register-password"
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    autoComplete="new-password"
                    minLength={6}
                    required
                  />
                  <InputGroupAddon align="inline-end">
                    <InputGroupButton
                      type="button"
                      variant="ghost"
                      size="icon-sm"
                      onClick={() => setShowPassword((p) => !p)}
                      aria-label={showPassword ? "Ocultar senha" : "Mostrar senha"}
                    >
                      <HugeiconsIcon
                        icon={showPassword ? ViewOffIcon : EyeIcon}
                        strokeWidth={2}
                      />
                    </InputGroupButton>
                  </InputGroupAddon>
                </InputGroup>
                <FieldDescription>Mínimo de 6 caracteres</FieldDescription>
              </Field>
              <Field>
                <FieldLabel htmlFor="register-confirm">Confirmar Senha</FieldLabel>
                <InputGroup>
                  <InputGroupInput
                    id="register-confirm"
                    type={showConfirmPassword ? "text" : "password"}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    autoComplete="new-password"
                    required
                  />
                  <InputGroupAddon align="inline-end">
                    <InputGroupButton
                      type="button"
                      variant="ghost"
                      size="icon-sm"
                      onClick={() => setShowConfirmPassword((p) => !p)}
                      aria-label={showConfirmPassword ? "Ocultar senha" : "Mostrar senha"}
                    >
                      <HugeiconsIcon
                        icon={showConfirmPassword ? ViewOffIcon : EyeIcon}
                        strokeWidth={2}
                      />
                    </InputGroupButton>
                  </InputGroupAddon>
                </InputGroup>
                {confirmPassword.length > 0 && (
                  <p
                    role="status"
                    className={cn(
                      "text-sm mt-2 flex items-center gap-1.5 rounded-lg px-3 py-2 font-medium transition-colors",
                      password === confirmPassword
                        ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                        : "bg-amber-500/10 text-amber-600 dark:text-amber-400"
                    )}
                  >
                    {password === confirmPassword ? (
                      <>Senhas coincidem</>
                    ) : (
                      <>As senhas não coincidem</>
                    )}
                  </p>
                )}
              </Field>
            </FieldGroup>
            {message && (
              <p
                role="alert"
                className={cn(
                  "text-sm rounded-lg px-3 py-2",
                  message.type === "success"
                    ? "bg-primary/10 text-primary"
                    : "bg-destructive/10 text-destructive"
                )}
              >
                {message.text}
              </p>
            )}
          </CardContent>
          <CardFooter className="flex flex-col gap-3 pt-0">
            <Button type="submit" className="w-full min-h-10 touch-manipulation" disabled={loading}>
              {loading ? "Criando…" : "Criar Conta"}
            </Button>
            <p className="text-center text-sm text-muted-foreground">
              Já tem uma conta?{" "}
              <Link to="/login" className="text-primary underline underline-offset-4 hover:no-underline">
                Entrar
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
    </div>
  )
}
