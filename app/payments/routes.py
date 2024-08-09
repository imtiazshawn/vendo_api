from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer

from app.auth.token import verify_token
from app.services.dbServices import connect_to_database
from app.utils.date_convert import format_datetime
from app.payments.schemas import PaymentResponse, PaymentCreate

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


@router.post("/payments", response_model=PaymentResponse)
async def process_payment(payment: PaymentCreate, token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
        username = payload.get("sub")

        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO Payments (orderId, amount, paymentMethod, paymentStatus, createdAt, updatedAt)
            VALUES (?, ?, ?, ?, GETDATE(), GETDATE())
        """,
            (
                payment.order_id,
                payment.amount,
                payment.payment_method,
                payment.payment_status,
            ),
        )
        conn.commit()

        cursor.execute("SELECT paymentId FROM Payments WHERE paymentId=@@IDENTITY")
        new_payment_id = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT paymentId, orderId, amount, paymentMethod, paymentStatus, createdAt, updatedAt
            FROM Payments WHERE paymentId=?
        """,
            (new_payment_id,),
        )
        payment_data = cursor.fetchone()

        cursor.close()
        conn.close()

        if not payment_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Failed to process payment",
            )

        return {
            "payment_id": payment_data[0],
            "order_id": payment_data[1],
            "amount": payment_data[2],
            "payment_method": payment_data[3],
            "payment_status": payment_data[4],
            "created_at": format_datetime(payment_data[5]),
            "updated_at": format_datetime(payment_data[6]),
        }
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing payment",
        )


@router.get("/payments/{payment_id}", response_model=PaymentResponse)
async def get_payment_details(payment_id: int, token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
        username = payload.get("sub")

        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM Payments WHERE paymentId=?", (payment_id,))
        payment = cursor.fetchone()

        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found"
            )

        cursor.close()
        conn.close()

        return {
            "payment_id": payment[0],
            "order_id": payment[1],
            "amount": payment[2],
            "payment_method": payment[3],
            "payment_status": payment[4],
            "created_at": format_datetime(payment[5]),
            "updated_at": format_datetime(payment[6]),
        }
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching payment details",
        )
