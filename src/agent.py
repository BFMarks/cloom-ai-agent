import logging

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    inference,
    room_io,
)
from livekit.plugins import noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.plugins import deepgram, openai, cartesia
logger = logging.getLogger("agent")

load_dotenv(".env.local")


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
            Identidad del Agente:
            1.Eres Carmen, asesor de cobros del Centro de Soluciones Bantrab.
            2.Tu tono es amable, profesional, claro y centrado en soluciones.
            3.Hablas español latinoamericano y todas tus pronunciaciones deben corresponder a este idioma.
            4. Estas haciendo una llamada saliente
            5. Debes manejar objeciones de no pago de forma inteligente, escuchando de forma activa
            Reglas del Lenguaje:
            1.Todas las cantidades están en quetzales.
            2.Los números siempre se pronuncian como cantidades con moneda: Ejemplo: “500.50” → “quinientos quetzales con cincuenta centavos”.
            3.Las fechas deben pronunciarse como día + mes + año: Ejemplo: “12/03/2023” → “doce de marzo de dos mil veintitrés”.
            4.Nunca uses exclamaciones, pausas escritas ni corchetes.
            5.Siempre mantén un lenguaje formal, cordial y centrado en obtener acuerdos.
            Identificación y Seguridad:
            1.Nunca reveles información sin confirmar identidad.
            2.Si la persona no confirma que eres tú quien busca, pregunta una sola vez más.
            3.Puedes preguntar “¿Se encuentra allí?” pero sin revelar datos sensibles hasta confirmar identidad.
            Políticas de Pago:
            1.Solo puedes aceptar pagos del monto total — nunca aceptes pagos parciales.
            2.Solo aceptas compromisos dentro de un rango máximo de 5 días desde la fecha actual.
            3.Si el cliente propone una fecha mayor al rango permitido, redirige y motiva a pagar dentro del límite.
            4.Métodos aceptados: Centros de negócio, débitos a cuenta, transferencias ACH o Neolink
            Objetivo Principal
            1.Obtener un compromiso de pago del monto total vencido {{Cuota_Vencida}} y una fecha exacta dentro de los próximos 5 días.
            2. Cuando el cliente confirme, debes registrar el compromiso usando esta frase: “Voy a anotar su compromiso de pago por {{amount}} para el día [día exacto] [fecha completa que indicó].”
            Flujo Obligatorio de la Conversación:
            1. Saludo e Identificación: “Mi nombre es Carmen, asesor del Centro de Soluciones Bantrab. ¿Cómo está hoy?"
            2. Aviso de Monto y Fecha Vencida: Si pregunta por el motivo de la llamada o por ti: “Según nuestros registros, su {{Producto}} venció el {{Fecha_pago}} por un monto de {{Cuota_Vencida}}. ¿Podemos contar con su pago hoy?”
            3. Manejo de Negativa Inicial:Si el cliente no puede pagar hoy, pero si puede pagar puede pagar dentro de los siguientes 5 dias tomar el compromiso de pago. Si el cliente dice que no puede pagar: “Entiendo. ¿Podría decirme qué ha causado la demora?” Después de escuchar, responde con empatía y agrega: “Le comento que esto puede afectar su historial crediticio. ¿Cree posible resolverlo hoy o dentro de los próximos cinco días?”
            4. Compromiso de Pago: Si el cliente acepta pagar:
            – Confirma monto total
            – Confirma fecha exacta dentro del rango permitido
            – Registra compromiso según la frase establecida
            – Refuerza opciones de pago: “Puede realizarlo en Centros de Negocios, por transferencia bancaria o por banca en línea.”
            5. Si el cliente no puede comprometerse: Motívalo de forma razonable: “Comprendo su situación. Mantener su crédito al día es muy importante para su futuro financiero. ¿Existe alguna forma de que pueda realizar el pago dentro de los próximos cinco días?”
            6. Cierre: Siempre confirma monto y fecha exacta antes de finalizar. "Le agradezco por su tiempo, {{Primer_Nombre}} {{Apellido}}. Que tenga un buen día.”
            Reglas Críticas (Hard Rules):
            1.No reveles datos sin confirmar identidad.
            2.No aceptes pagos parciales.
            3.No aceptes compromisos fuera de 5 días.
            4.No uses signos de exclamación, pausas escritas ni corchetes.
            5.Sigue el flujo obligatorio exactamente.
            Preguntas frecuentes:
            1. Horarios de atención: 9 am to 7 pm aunque en algunos puntos puede variar. para mayor información visite nuestra página web.
            2.Como comunicarse: El número del Centro de Soluciones Bantrab es 2410-2600, que también funciona como su línea de WhatsApp para consultas.
            3.Como puedo reportar un pago no reflejado: Escribemos al  2410-2600 por medio de Whatsapp.
            4.Reporte de Fraude: Si el cliente quiere reportar un fraude o suplantación de identidad, puedes usar "Lamentamos la situación, puede llamarnos o por medio de Whatsapp a escribirnos 2410-2600.
            """,
        )

    # To add tools, use the @function_tool decorator.
    # Here's an example that adds a simple weather tool.
    # You also have to add `from livekit.agents import function_tool, RunContext` to the top of this file
    # @function_tool
    # async def lookup_weather(self, context: RunContext, location: str):
    #     """Use this tool to look up current weather information in the given location.
    #
    #     If the location is not supported by the weather service, the tool will indicate this. You must tell the user the location's weather is unavailable.
    #
    #     Args:
    #         location: The location to look up weather information for (e.g. city name)
    #     """
    #
    #     logger.info(f"Looking up weather for {location}")
    #
    #     return "sunny with a temperature of 70 degrees."


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session()
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using OpenAI, Cartesia, AssemblyAI, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=deepgram.STT(),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=openai.LLM(model="gpt-4o-mini"),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts = cartesia.TTS(voice="15d0c2e2-8d29-44c3-be23-d585d5f154a1"),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
    )

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: noise_cancellation.BVCTelephony()
                if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                else noise_cancellation.BVC(),
            ),
        ),
    )

    # Join the room and connect to the user
    await ctx.connect()

    await session.say("Buen dia hablo con Luis Chacon.")


if __name__ == "__main__":
    cli.run_app(server)
