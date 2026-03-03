import { Link } from "react-router-dom"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Field, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import {
  InputGroup,
  InputGroupInput,
  InputGroupAddon,
  InputGroupButton,
} from "@/components/ui/input-group"
import { cn } from "@/lib/utils"
import { useLogin } from "./hook"
import { HugeiconsIcon } from "@hugeicons/react"
import { EyeIcon, ViewOffIcon } from "@hugeicons/core-free-icons"

export function Login() {
  const {
    username,
    setUsername,
    password,
    setPassword,
    showPassword,
    setShowPassword,
    message,
    loading,
    version,
    handleSubmit,
  } = useLogin()

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
          <CardTitle className="text-2xl">Croma</CardTitle>
          <CardDescription>
            Sistema de Monitoramento de Impressora 3D
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4 pb-6">
            <FieldGroup>
              <Field>
                <FieldLabel htmlFor="login-username">Usuário</FieldLabel>
                <Input
                  id="login-username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Digite seu usuário"
                  autoComplete="username"
                  required
                />
              </Field>
              <Field>
                <FieldLabel htmlFor="login-password">Senha</FieldLabel>
                <InputGroup>
                  <InputGroupInput
                    id="login-password"
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Digite sua senha"
                    autoComplete="current-password"
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
              {loading ? "Entrando…" : "Entrar"}
            </Button>
            <p className="text-center text-sm text-muted-foreground">
              Não tem uma conta?{" "}
              <Link to="/register" className="text-primary underline underline-offset-4 hover:no-underline">
                Criar conta
              </Link>
            </p>
            {version && (
              <div className="flex justify-center pt-1">
                <Badge variant="outline" className="text-muted-foreground font-mono text-xs">
                  Versão: {version}
                </Badge>
              </div>
            )}
          </CardFooter>
        </form>
      </Card>
    </div>
  )
}
